import pytest
import numpy as np

from astropy.io import fits
from astropy.table import Column
from astropop.file_collection import FitsFileGroup, list_fits_files
from astropop.testing import assert_is_instance, assert_equal, \
                             assert_in


@pytest.fixture(scope='session')
def tmpdir(tmp_path_factory):
    fn = tmp_path_factory.mktemp('filegroups')
    files = {}
    for i in ('fits', 'fz', 'fits.gz', 'fts', 'fit'):
        folder = fn / i.replace('.', '_')
        folder.mkdir()
        files[i] = create_test_files(folder, extension=i)

    # Also create the images on the custom HDU

    tmpdir = fn / 'custom_hdu'
    tmpdir.mkdir()
    flist = []
    for i in range(10):
        fname = tmpdir / f'bias_{i+1}.fits'
        if fname.is_file():
            continue
        hdr = fits.Header({'obstype': 'bias',
                           'exptime': 0.0001,
                           'observer': 'Galileo Galileo',
                           'object': 'bias',
                           'filter': ''})
        hdul = fits.HDUList([
            fits.PrimaryHDU(),
            fits.ImageHDU(np.ones((8, 8), dtype=np.int16), hdr,
                          name='image')
            ])
        hdul.writeto(fname)
        flist.append(str(fname))
    files['custom_hdu'] = flist

    files['custom'] = []
    folder = fn / 'custom'
    folder.mkdir()
    for i in ('myfits', 'otherfits'):
        f = create_test_files(folder, extension=i)
        files['custom'].extend(f)
        files[i] = f

    return fn, files


def create_test_files(tmpdir, extension='fits'):
    """Create dummy test files for testing."""
    files_list = []
    # create 10 bias files
    for i in range(10):
        iname = f'bias_{i}.{extension}'
        fname = tmpdir / iname
        if fname.is_file():
            continue
        hdr = fits.Header({'obstype': 'bias',
                           'exptime': 0.0001,
                           'observer': 'Galileo Galileo',
                           'object': 'bias',
                           'filter': '',
                           'space key': 1,
                           'image': iname})
        hdu = fits.PrimaryHDU(np.ones((8, 8), dtype=np.int16), hdr)
        hdu.writeto(fname)
        files_list.append(str(fname))

    # create 10 flat V files
    for i in range(10):
        iname = f'flat_{i}_v.{extension}'
        fname = tmpdir / iname
        if fname.is_file():
            continue
        hdr = fits.Header({'obstype': 'flat',
                           'exptime': 10.0,
                           'observer': 'Galileo Galileo',
                           'object': 'flat',
                           'filter': 'V',
                           'space key': 1,
                           'image': iname})
        hdu = fits.PrimaryHDU(np.ones((8, 8), dtype=np.int16), hdr)
        hdu.writeto(fname)
        files_list.append(str(fname))

    # create 10 object V files
    for i in range(10):
        iname = f'object_{i}_v.{extension}'
        fname = tmpdir / iname
        if fname.is_file():
            continue
        hdr = fits.Header({'obstype': 'science',
                           'exptime': 1.0,
                           'observer': 'Galileo Galileo',
                           'object': 'Moon',
                           'filter': 'V',
                           'space key': 1,
                           'image': iname})
        hdu = fits.PrimaryHDU(np.ones((8, 8), dtype=np.int16), hdr)
        hdu.writeto(fname)
        files_list.append(str(fname))

    return files_list


class Test_FitsFileGroup():
    def test_fg_creation_empty(self):
        with pytest.raises(ValueError):
            FitsFileGroup()
        # test the hidden option to create uninitialized group.
        fg = FitsFileGroup(__uninitialized=True)
        assert_is_instance(fg, FitsFileGroup)

    def test_fg_create_filegroup(self, tmpdir):
        tmpdir, flist = tmpdir
        fg = FitsFileGroup(location=tmpdir/'fits_gz', compression=True)
        assert_is_instance(fg, FitsFileGroup)
        assert_equal(len(fg), 30)
        assert_equal(sorted(fg.files), sorted(flist['fits.gz']))

    def test_fg_create_filegroup_without_compression(self, tmpdir):
        tmpdir, flist = tmpdir
        fg = FitsFileGroup(location=tmpdir/'fits', compression=False)
        assert_is_instance(fg, FitsFileGroup)
        assert_equal(len(fg), 30)
        assert_equal(sorted(fg.files), sorted(flist['fits']))

        #Default is False
        fg = FitsFileGroup(location=tmpdir/'fits')
        assert_is_instance(fg, FitsFileGroup)
        assert_equal(len(fg), 30)
        assert_equal(sorted(fg.files), sorted(flist['fits']))

    def test_fg_creation_files(self, tmpdir):
        tmpdir, flist = tmpdir
        fg = FitsFileGroup(files=flist['fits'])
        assert_is_instance(fg, FitsFileGroup)
        assert_equal(len(fg), 30)
        assert_equal(sorted(fg.files), sorted(flist['fits']))

    def test_fg_creation_no_std_extension(self, tmpdir):
        tmpdir, flist = tmpdir
        fg = FitsFileGroup(location=tmpdir/'fts')
        assert_is_instance(fg, FitsFileGroup)
        assert_equal(len(fg), 30)
        assert_equal(sorted(fg.files), sorted(flist['fts']))

        fg = FitsFileGroup(location=tmpdir/'fit')
        assert_is_instance(fg, FitsFileGroup)
        assert_equal(len(fg), 30)
        assert_equal(sorted(fg.files), sorted(flist['fit']))

        fg = FitsFileGroup(location=tmpdir/'fz')
        assert_is_instance(fg, FitsFileGroup)
        assert_equal(len(fg), 30)
        assert_equal(sorted(fg.files), sorted(flist['fz']))

    def test_fg_creation_glob_include_exclude(self, tmpdir):
        tmpdir, flist = tmpdir
        # only bias
        fg = FitsFileGroup(location=tmpdir/'fits', glob_include='*bias*')
        assert_is_instance(fg, FitsFileGroup)
        assert_equal(len(fg), 10)
        assert_equal(sorted(fg.files), sorted(flist['fits'][:10]))

        # everything except bias
        fg = FitsFileGroup(location=tmpdir/'fits', glob_exclude='*bias*')
        assert_is_instance(fg, FitsFileGroup)
        assert_equal(len(fg), 20)
        assert_equal(sorted(fg.files), sorted(flist['fits'][10:]))

    @pytest.mark.parametrize('hdu', [1, 'image'])
    def test_fg_creation_custom_hdu(self, tmpdir, hdu):
        tmpdir, flist = tmpdir
        fg = FitsFileGroup(location=tmpdir/'custom_hdu', ext=hdu)
        assert_is_instance(fg, FitsFileGroup)
        assert_equal(len(fg), 10)
        assert_equal(sorted(fg.files), sorted(flist['custom_hdu']))
        for k in ('object', 'exptime', 'observer', 'filter'):
            assert_in(k, fg.summary.colnames)
        for i in fg.summary:
            assert_equal(i['object'], 'bias')

    def test_fg_filtered_single_key(self, tmpdir):
        tmpdir, flist = tmpdir
        fg = FitsFileGroup(location=tmpdir/'fits', compression=False)
        bias_files = flist['fits'][:10]
        flat_files = flist['fits'][10:20]
        sci_files = flist['fits'][20:]

        # object keyword
        fg_b = fg.filtered({'object': 'bias'})
        assert_equal(len(fg_b), 10)
        assert_equal(sorted(fg_b.files),
                     sorted(bias_files))

        # filter keyword
        fg_v = fg.filtered({'filter': 'V'})
        assert_equal(len(fg_v), 20)
        assert_equal(sorted(fg_v.files),
                     sorted(flat_files + sci_files))

        # Hierarch key with space
        fg_s = fg.filtered({'space key': 1})
        assert_equal(len(fg_s), 30)
        assert_equal(sorted(fg_s.files),
                     sorted(bias_files + flat_files + sci_files))

    def test_fg_filtered_multiple_key(self, tmpdir):
        tmpdir, flist = tmpdir
        fg = FitsFileGroup(location=tmpdir/'fits', compression=False)
        nfg = fg.filtered({'object': 'Moon',
                           'exptime': 1.0,
                           'image': 'object_4_v.fits'})
        assert_equal(len(nfg), 1)
        assert_equal(nfg.files, [flist['fits'][24]])

    def test_fg_filtered_empty(self, tmpdir):
        tmpdir, flist = tmpdir
        fg = FitsFileGroup(location=tmpdir/'fits', compression=False)

        # non existing key
        nfg = fg.filtered({'NON-EXISTING': 1})
        assert_is_instance(nfg, FitsFileGroup)
        assert_equal(len(nfg), 0)
        assert_equal(nfg.files, [])

        # existing but not matched
        nfg = fg.filtered({'object': 'Sun'})
        assert_is_instance(nfg, FitsFileGroup)
        assert_equal(len(nfg), 0)
        assert_equal(nfg.files, [])

    def test_fg_getitem_column(self, tmpdir):
        tmpdir, flist = tmpdir
        fg = FitsFileGroup(location=tmpdir/'fits', compression=False)
        obj_column = fg['object']
        assert_equal(sorted(obj_column),
                     sorted(['bias']*10+['flat']*10+['Moon']*10))
        assert_is_instance(obj_column, Column)

    def test_fg_getitem_single_file(self, tmpdir):
        tmpdir, flist = tmpdir
        fg = FitsFileGroup(location=tmpdir/'fits', compression=False)
        row = fg[1]
        assert_is_instance(row, FitsFileGroup)
        assert_equal(len(row), 1)
        assert_equal(row.files, [flist['fits'][1]])

    def test_fg_getitem_slice(self, tmpdir):
        tmpdir, flist = tmpdir
        fg = FitsFileGroup(location=tmpdir/'fits', compression=False)
        row = fg[2:5]
        assert_is_instance(row, FitsFileGroup)
        assert_equal(len(row), 3)
        assert_equal(row.files, flist['fits'][2:5])

    def test_fg_getitem_array_or_tuple(self, tmpdir):
        tmpdir, flist = tmpdir
        flist = flist['fits']
        files = [flist[2], flist[4]]
        fg = FitsFileGroup(location=tmpdir/'fits', compression=False)
        row = fg[2, 4]
        assert_is_instance(row, FitsFileGroup)
        assert_equal(len(row), 2)
        assert_equal(row.files, files)

        row = fg[[2, 4]]
        assert_is_instance(row, FitsFileGroup)
        assert_equal(len(row), 2)
        assert_equal(row.files, files)

        row = fg[(2, 4)]
        assert_is_instance(row, FitsFileGroup)
        assert_equal(len(row), 2)
        assert_equal(row.files, files)

        row = fg[np.array([2, 4])]
        assert_is_instance(row, FitsFileGroup)
        assert_equal(len(row), 2)
        assert_equal(row.files, files)

    def test_fg_getitem_empty(self, tmpdir):
        tmpdir, flist = tmpdir
        fg = FitsFileGroup(location=tmpdir/'fits', compression=False)
        row = fg[[]]
        assert_is_instance(row, FitsFileGroup)
        assert_equal(len(row), 0)
        assert_equal(row.files, [])

    def test_fg_getitem_keyerror(self, tmpdir):
        tmpdir, flist = tmpdir
        fg = FitsFileGroup(location=tmpdir/'fits', compression=False)
        with pytest.raises(KeyError):
            fg['NonExistingKey']


class Test_ListFitsFiles():
    def test_list_custom_extension(self, tmpdir):
        tmpdir, flist = tmpdir
        found_files = list_fits_files(tmpdir/'custom',
                                      fits_extensions='.myfits')
        assert_equal(sorted(found_files), sorted(flist['myfits']))

        found_files = list_fits_files(tmpdir/'custom',
                                      fits_extensions=['.myfits', '.otherfits'])
        assert_equal(sorted(found_files), sorted(flist['custom']))

    @pytest.mark.parametrize('ext', ['fits', 'fz', 'fit', 'fts'])
    def test_list_no_extension(self, tmpdir, ext):
        tmpdir, flist = tmpdir
        found_files = list_fits_files(tmpdir/f'{ext}')
        assert_equal(sorted(found_files), sorted(flist[ext]))

    def test_list_glob_include(self, tmpdir):
        tmpdir, flist = tmpdir
        found_files = list_fits_files(tmpdir/'fits', glob_include='*bias*')
        # must find only bias
        assert_equal(sorted(found_files), sorted(flist['fits'][:10]))

    def test_list_glob_exclude(self, tmpdir):
        tmpdir, flist = tmpdir
        found_files = list_fits_files(tmpdir/'fits', glob_exclude='*bias*')
        # find everything except bias
        assert_equal(sorted(found_files), sorted(flist['fits'][10:]))
