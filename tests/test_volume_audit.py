import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from research.volume_metrology import axis_correlations, block_mean, chord_summary, measure
from research.volume_audit import audit_box, load_box, run


def record():
    return dict(id='example', specimen='synthetic', path='mask.npy',
                unit='um', spacing_zyx=[.1,.2,.3], foreground=1, background=0,
                tie_rule='foreground', roi_zyx=[[0,32]]*3,
                roi_reason='Fixed known-answer box', phase_definition='Synthetic binary phases',
                mask_authority='Generated test, not experimental segmentation')


def test_fft_matches_direct_nonperiodic_pairs():
    x=np.random.default_rng(8).normal(size=(8,10,12))
    centred=x-x.mean()
    for axis,c in enumerate(axis_correlations(x,chunk_lines=3)):
        for lag,actual in enumerate(c):
            a=[slice(None)]*3; b=a.copy()
            a[axis]=slice(0,x.shape[axis]-lag); b[axis]=slice(lag,None)
            expected=np.mean(centred[tuple(a)]*centred[tuple(b)])/x.var()
            np.testing.assert_allclose(actual,expected,atol=1e-12)


def test_complement_and_physical_spacing():
    x=np.random.default_rng(3).integers(0,2,(16,16,16))
    a=measure(x,[1,2,3],binary=True)
    b=measure(1-x,[2,4,6],binary=True)
    for key in ('half_height','chord_length'):
        np.testing.assert_allclose(b[key],2*a[key])


def test_complete_chords_do_not_join_faces():
    x=np.broadcast_to([0,0,1,1,1,0,0,0],(4,4,8))
    result=chord_summary(x,[1,1,2])
    assert result['chord_length']==6
    assert result['complete_chords']==16
    assert result['censored_boundary_runs']==96


def test_integration_preserves_mean_but_ties_can_change_binary_fraction():
    x=np.indices((32,32,32)).sum(axis=0)%2
    np.testing.assert_allclose(block_mean(x,2),.5)
    rows=audit_box(x,record())
    assert len(rows)==15
    assert rows[1]['mean_value']==.5
    assert rows[2]['mean_value']==1
    assert np.isnan(rows[2]['half_height'])
    assert rows[2]['tie_fraction']==1
    assert all(abs(r['integration_mean_error'])<1e-12 for r in rows)
    r=record(); r['tie_rule']='background'
    assert audit_box(x,r)[2]['mean_value']==0


def test_unknown_labels_invalidate_all_crops():
    x=np.zeros((32,32,32),dtype=int); x[0,0,0]=7
    rows=audit_box(x,record())
    assert all(r['unknown_voxels_in_full_box']==1 for r in rows)
    assert all(r['half_height_status'].startswith('ineligible') for r in rows)


def test_constant_field_and_bad_input():
    assert np.isnan(measure(np.zeros((8,8,8)),[1,1,1])['half_height'])
    with unittest.TestCase().assertRaises(ValueError): block_mean(np.zeros((8,8)),2)
    with unittest.TestCase().assertRaises(ValueError): block_mean(np.zeros((8,8,8)),3)
    with unittest.TestCase().assertRaises(ValueError): measure(np.zeros((8,8,8)),[0,1,1])


def test_tiff_npy_and_roi_checks(tmp_path):
    x=np.random.default_rng(4).integers(0,2,(32,32,32),dtype=np.uint8)
    np.save(tmp_path/'mask.npy',x)
    pages=[Image.fromarray(p) for p in x]
    pages[0].save(tmp_path/'mask.tif',save_all=True,append_images=pages[1:])
    for suffix in ('npy','tif'):
        np.testing.assert_array_equal(load_box(tmp_path/f'mask.{suffix}',[[0,32]]*3),x)
        with unittest.TestCase().assertRaises(ValueError): load_box(tmp_path/f'mask.{suffix}',[[1,33]]*3)


def test_report_manifest_and_no_overwrite(tmp_path):
    np.save(tmp_path/'mask.npy',np.random.default_rng(4).integers(0,2,(32,32,32)))
    r=record(); r['id']='<script>test</script>'
    plan=tmp_path/'plan.json'
    plan.write_text(json.dumps(dict(source='synthetic',license='test',records=[r])))
    result=run(plan,tmp_path/'result')
    assert '&lt;script&gt;test&lt;/script&gt;' in result.read_text()
    assert '<script>test</script>' not in result.read_text()
    manifest=json.loads((result.parent/'manifest.json').read_text())
    assert 'path' not in manifest['records'][0]
    assert len(manifest['records'][0]['sha256'])==64
    with unittest.TestCase().assertRaises(FileExistsError): run(plan,tmp_path/'result')
    r['sha256']='wrong'
    plan.write_text(json.dumps(dict(source='synthetic',license='test',records=[r])))
    with unittest.TestCase().assertRaisesRegex(ValueError,'changed'): run(plan,tmp_path/'other')


def load_tests(loader, tests, pattern):
    suite=unittest.TestSuite()
    for name,fn in list(globals().items()):
        if not name.startswith('test_') or not callable(fn): continue
        def call(fn=fn):
            if fn.__code__.co_argcount:
                with tempfile.TemporaryDirectory() as directory: fn(Path(directory))
            else: fn()
        suite.addTest(unittest.FunctionTestCase(call,description=name))
    return suite


def test_slab_analytic_covariance_and_unresolved_axes():
    x=np.zeros((32,32,32)); x[:,:,8:24]=1
    c=axis_correlations(x)
    r=np.arange(9)
    # n-r valid pairs; 2r cross one of the two interfaces. A mismatch
    # contributes -1 instead of +1, giving (n-r-4r)/(n-r).
    np.testing.assert_allclose(c[2][:9],(32-5*r)/(32-r),atol=1e-12)
    np.testing.assert_allclose(c[0],1,atol=1e-12)
    result=measure(x,[1,1,1],binary=True)
    assert np.isnan(result['half_height'])
    np.testing.assert_allclose(result['half_height_x'],3.546875)
    assert result['chord_length']==16


def test_cuboid_axis_permutation_and_mirror():
    x=np.zeros((32,32,32)); x[10:18,8:20,6:22]=1
    a=measure(x,[1,1,1])
    assert a['half_height_z']<a['half_height_y']<a['half_height_x']
    b=measure(x.transpose(2,1,0),[1,1,1])
    np.testing.assert_allclose(a['half_height_x'],b['half_height_z'])
    np.testing.assert_allclose(a['half_height_z'],b['half_height_x'])
    for c,d in zip(axis_correlations(x),axis_correlations(x[::-1,::-1,::-1])):
        np.testing.assert_allclose(c,d,atol=1e-12)


def test_sphere_resolution_mean_and_source_immutability():
    z,y,x=np.indices((32,32,32))
    mask=((z-15.5)**2+(y-15.5)**2+(x-15.5)**2<7**2).astype(np.uint8)
    before=mask.copy()
    a=measure(mask,[1,1,1])
    np.testing.assert_allclose([a['half_height_z'],a['half_height_y']],a['half_height_x'])
    rows=audit_box(mask,record())
    np.testing.assert_array_equal(mask,before)
    for fraction in (1.,.75,.5):
        group=[r for r in rows if r['crop_fraction']==fraction]
        native=group[0]['mean_value']
        for r in group:
            if r['stage']=='integrated': assert r['mean_value']==native
