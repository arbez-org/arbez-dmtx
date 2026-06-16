"""Force a Python-version-agnostic platform wheel tag: py3-none-<platform>.

The package is pure ctypes (no compiled extension to bind a CPython ABI) but it
ships a native libdmtx, so the wheel must be platform-tagged yet importable on
every Python 3.10-3.14 including free-threaded 3.13t/3.14t. The default
bdist_wheel would tag an impure-but-extension-less package per-interpreter; this
override pins ``py3``/``none`` so ONE wheel per platform serves all Pythons.

The *platform* portion of the tag (manylinux_*/macosx_*) is normalized in CI by
the `wheel tags` retag step after the bundled lib is built in the right
environment — auditwheel/delocate can't retag a no-extension wheel — so we don't
compute it here.
"""
from setuptools import setup

try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

    class bdist_wheel(_bdist_wheel):
        def finalize_options(self):
            super().finalize_options()
            self.root_is_pure = False  # -> platform tag, ships the native lib

        def get_tag(self):
            _python, _abi, plat = super().get_tag()
            return "py3", "none", plat  # any Python 3, no ABI lock

    cmdclass = {"bdist_wheel": bdist_wheel}
except ImportError:
    cmdclass = {}

setup(cmdclass=cmdclass)
