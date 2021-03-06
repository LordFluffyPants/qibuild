.. _qibuild-test-suite:

Running qiBuild test suite
==========================


Installing required packages
----------------------------

You need to install the following Python packages to run the test suite:

* python-tox

Althought qiBuild is a cross-platform, running the test suite on Windows
with Visual Studio is quite painful. (Patches welcome ...)


All in one step
---------------

Simply go to the root directory of qibuild and run:

.. code-block:: console

    tox -c python/tox.ini

Note: if you are on a distribution where ``/usr/bin/python`` is Python3,
you should use

.. code-block:: console

    tox2 -c python/tox.ini


This will use pylint to find obvious errors (like variables referenced
before assignement, missing imports, and so on), then will run
the automatic tests, and finally run a coverage report.

Sometime pylint is mistaken, you can fix this by adding a small comment
to disable the check, using the pylint error code:

.. code-block:: python

    # pylint: disable-msg=E1101

Running test suite
------------------

This is on a build farm but only for linux and python2.7, so it is possible
that some tests will fail.

If you do find a failing test, please open a bug.

If you find a bug, a nice way to make it easier to fix it is to write a
failing test and mark it as 'skipped'

.. code-block:: python

  @pytest.skip("See bug # ....")
  def test_subtle_bug(self):
     res = do_something_complicated()
     # Should be 42 but for some reason is 41 ...
     self.assertTrue(res, 42)


This way when the bug is fixed we just have to remove the ``@pytest.skip``
and we are sure the bug never occurs again.

Note: some tests are slow to run, you can mark them with

.. code-block:: python

  @pytest.mark.slow
  def test_slow_command(self):
      # something long going on here ...

And then run the tests with

.. code-block:: console

    cd python/
    py.test -k -slow


Running only some tests
+++++++++++++++++++++++

You can use ``py.test`` (or ``py.test2``) with

  * Just for a given python package:

  .. code-block:: console

      cd python
      py.test qisrc

  * Just for a given test file:

  .. code-block:: console

     py.test qisrc/test/test_git.py

  * Just for a given test name:

  .. code-block:: console

     py.test qisrc/test/test_git.py -k set_tracking_branch

Note about ipdb
++++++++++++++++


If you are using ``ipdb`` to insert break points in the code like this:

.. code-block:: python

    # in foo.py
    def test_my_complicated_function():
        import ipdb; ipdb.set_trace()


You will get an error message like this if you run

.. code-block:: console

  $ py.test foo.py
  ValueError: fallback required, but not specified

(This may be a bug in ``ipdb``, ``py.test`` or both ...)

The solution is to use the ``-s`` option of py.test:


.. code-block:: console

  $ py.test foo.py -s
