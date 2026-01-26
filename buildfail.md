18:31:42.705 Running build in Portland, USA (West) – pdx1
18:31:42.706 Build machine configuration: 2 cores, 8 GB
18:31:42.807 Cloning github.com/kali-Gaurav/route-master-final (Branch: testfolder_v4, Commit: 81d31d6)
18:31:42.808 Previous build caches not available.
18:31:46.137 Warning: Failed to fetch one or more git submodules
18:31:46.137 Cloning completed: 3.330s
18:31:46.676 Running "vercel build"
18:31:47.640 Vercel CLI 50.4.10
18:31:48.202 Installing dependencies...
18:31:48.579 Using CPython 3.14.2
18:31:48.982 Resolved 38 packages in 398ms
18:31:49.006 Downloading pydantic-core (2.0MiB)
18:31:49.010 Downloading numpy (15.6MiB)
18:31:49.146  Downloaded pydantic-core
18:31:49.339    Building aiohttp==3.9.1
18:31:49.574  Downloaded numpy
18:31:49.680    Building pandas==2.0.0
18:32:16.607       Built aiohttp==3.9.1
18:33:18.020   × Failed to build `pandas==2.0.0`
18:33:18.021   ├─▶ The build backend returned an error
18:33:18.027   ╰─▶ Call to `setuptools.build_meta:__legacy__.build_wheel` failed (exit
18:33:18.028       status: 1)
18:33:18.028 
18:33:18.028       [stdout]
18:33:18.028       running bdist_wheel
18:33:18.029       running build
18:33:18.029       running build_py
18:33:18.029       creating build/lib.linux-x86_64-cpython-314/pandas
18:33:18.029       copying pandas/__init__.py -> build/lib.linux-x86_64-cpython-314/pandas
18:33:18.029       copying pandas/_typing.py -> build/lib.linux-x86_64-cpython-314/pandas
18:33:18.029       copying pandas/_version.py -> build/lib.linux-x86_64-cpython-314/pandas
18:33:18.029       copying pandas/conftest.py -> build/lib.linux-x86_64-cpython-314/pandas
18:33:18.029       copying pandas/testing.py -> build/lib.linux-x86_64-cpython-314/pandas
18:33:18.029       creating build/lib.linux-x86_64-cpython-314/pandas/_config
18:33:18.029       copying pandas/_config/__init__.py ->
18:33:18.029       build/lib.linux-x86_64-cpython-314/pandas/_config
18:33:18.029       copying pandas/_config/config.py ->
18:33:18.029       build/lib.linux-x86_64-cpython-314/pandas/_config
18:33:18.029       copying pandas/_config/dates.py ->
18:33:18.029       build/lib.linux-x86_64-cpython-314/pandas/_config
18:33:18.029       copying pandas/_config/display.py ->
18:33:18.029       build/lib.linux-x86_64-cpython-314/pandas/_config
18:33:18.029       copying pandas/_config/localization.py ->
18:33:18.029       build/lib.linux-x86_64-cpython-314/pandas/_config
18:33:18.029       creating build/lib.linux-x86_64-cpython-314/pandas/_libs
18:33:18.029       copying pandas/_libs/__init__.py ->
18:33:18.030       build/lib.linux-x86_64-cpython-314/pandas/_libs
18:33:18.030       creating build/lib.linux-x86_64-cpython-314/pandas/_testing
18:33:18.030       copying pandas/_testing/__init__.py ->
18:33:18.030       build/lib.linux-x86_64-cpython-314/pandas/_testing
18:33:18.030       copying pandas/_testing/_hypothesis.py ->
18:33:18.030       build/lib.linux-x86_64-cpython-314/pandas/_testing
18:33:18.030       copying pandas/_testing/_io.py ->
18:33:18.030       build/lib.linux-x86_64-cpython-314/pandas/_testing
18:33:18.030       copying pandas/_testing/_random.py ->
18:33:18.030       build/lib.linux-x86_64-cpython-314/pandas/_testing
18:33:18.030       copying pandas/_testing/_warnings.py ->
18:33:18.030       build/lib.linux-x86_64-cpython-314/pandas/_testing
18:33:18.030       copying pandas/_testing/asserters.py ->
18:33:18.030       build/lib.linux-x86_64-cpython-314/pandas/_testing
18:33:18.031       copying pandas/_testing/compat.py ->
18:33:18.031       build/lib.linux-x86_64-cpython-314/pandas/_testing
18:33:18.031       copying pandas/_testing/contexts.py ->
18:33:18.031       build/lib.linux-x86_64-cpython-314/pandas/_testing
18:33:18.031       creating build/lib.linux-x86_64-cpython-314/pandas/api
18:33:18.032       copying pandas/api/__init__.py ->
18:33:18.032       build/lib.linux-x86_64-cpython-314/pandas/api
18:33:18.032       creating build/lib.linux-x86_64-cpython-314/pandas/arrays
18:33:18.032       copying pandas/arrays/__init__.py ->
18:33:18.032       build/lib.linux-x86_64-cpython-314/pandas/arrays
18:33:18.032       creating build/lib.linux-x86_64-cpython-314/pandas/compat
18:33:18.032       copying pandas/compat/__init__.py ->
18:33:18.032       build/lib.linux-x86_64-cpython-314/pandas/compat
18:33:18.033       copying pandas/compat/_constants.py ->
18:33:18.033       build/lib.linux-x86_64-cpython-314/pandas/compat
18:33:18.033       copying pandas/compat/_optional.py ->
18:33:18.033       build/lib.linux-x86_64-cpython-314/pandas/compat
18:33:18.033       copying pandas/compat/compressors.py ->
18:33:18.033       build/lib.linux-x86_64-cpython-314/pandas/compat
18:33:18.033       copying pandas/compat/pickle_compat.py ->
18:33:18.033       build/lib.linux-x86_64-cpython-314/pandas/compat
18:33:18.033       copying pandas/compat/pyarrow.py ->
18:33:18.033       build/lib.linux-x86_64-cpython-314/pandas/compat
18:33:18.034       creating build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.034       copying pandas/core/__init__.py ->
18:33:18.034       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.034       copying pandas/core/accessor.py ->
18:33:18.034       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.034       copying pandas/core/algorithms.py ->
18:33:18.034       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.034       copying pandas/core/api.py ->
18:33:18.035       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.035       copying pandas/core/apply.py ->
18:33:18.035       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.035       copying pandas/core/arraylike.py ->
18:33:18.035       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.035       copying pandas/core/base.py ->
18:33:18.035       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.035       copying pandas/core/common.py ->
18:33:18.035       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.036       copying pandas/core/config_init.py ->
18:33:18.036       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.036       copying pandas/core/construction.py ->
18:33:18.036       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.036       copying pandas/core/flags.py ->
18:33:18.036       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.036       copying pandas/core/frame.py ->
18:33:18.036       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.036       copying pandas/core/generic.py ->
18:33:18.037       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.037       copying pandas/core/indexing.py ->
18:33:18.037       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.037       copying pandas/core/missing.py ->
18:33:18.037       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.037       copying pandas/core/nanops.py ->
18:33:18.037       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.037       copying pandas/core/resample.py ->
18:33:18.037       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.038       copying pandas/core/roperator.py ->
18:33:18.039       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.039       copying pandas/core/sample.py ->
18:33:18.039       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.039       copying pandas/core/series.py ->
18:33:18.039       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.039       copying pandas/core/shared_docs.py ->
18:33:18.040       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.040       copying pandas/core/sorting.py ->
18:33:18.040       build/lib.linux-x86_64-cpython-314/pandas/core
18:33:18.040       creating build/lib.linux-x86_64-cpython-314/pandas/errors
18:33:18.040       copying pandas/errors/__init__.py ->
18:33:18.040       build/lib.linux-x86_64-cpython-314/pandas/errors
18:33:18.041       creating build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.041       copying pandas/io/__init__.py ->
18:33:18.041       build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.041       copying pandas/io/_util.py ->
18:33:18.041       build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.041       copying pandas/io/api.py -> build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.041       copying pandas/io/clipboards.py ->
18:33:18.042       build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.042       copying pandas/io/common.py ->
18:33:18.042       build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.042       copying pandas/io/feather_format.py ->
18:33:18.042       build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.043       copying pandas/io/gbq.py -> build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.043       copying pandas/io/html.py -> build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.043       copying pandas/io/orc.py -> build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.043       copying pandas/io/parquet.py ->
18:33:18.043       build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.043       copying pandas/io/pickle.py ->
18:33:18.043       build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.044       copying pandas/io/pytables.py ->
18:33:18.044       build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.044       copying pandas/io/spss.py -> build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.044       copying pandas/io/sql.py -> build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.044       copying pandas/io/stata.py ->
18:33:18.044       build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.044       copying pandas/io/xml.py -> build/lib.linux-x86_64-cpython-314/pandas/io
18:33:18.045       creating build/lib.linux-x86_64-cpython-314/pandas/plotting
18:33:18.045       copying pandas/plotting/__init__.py ->
18:33:18.045       build/lib.linux-x86_64-cpython-314/pandas/plotting
18:33:18.045       copying pandas/plotting/_core.py ->
18:33:18.045       build/lib.linux-x86_64-cpython-314/pandas/plotting
18:33:18.045       copying pandas/plotting/_misc.py ->
18:33:18.045       build/lib.linux-x86_64-cpython-314/pandas/plotting
18:33:18.046       creating build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.046       copying pandas/tests/__init__.py ->
18:33:18.046       build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.046       copying pandas/tests/test_aggregation.py ->
18:33:18.046       build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.046       copying pandas/tests/test_algos.py ->
18:33:18.046       build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.047       copying pandas/tests/test_common.py ->
18:33:18.047       build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.047       copying pandas/tests/test_downstream.py ->
18:33:18.047       build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.047       copying pandas/tests/test_errors.py ->
18:33:18.047       build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.047       copying pandas/tests/test_expressions.py ->
18:33:18.047       build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.047       copying pandas/tests/test_flags.py ->
18:33:18.048       build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.048       copying pandas/tests/test_multilevel.py ->
18:33:18.048       build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.048       copying pandas/tests/test_nanops.py ->
18:33:18.048       build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.048       copying pandas/tests/test_optional_dependency.py ->
18:33:18.048       build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.048       copying pandas/tests/test_register_accessor.py ->
18:33:18.049       build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.049       copying pandas/tests/test_sorting.py ->
18:33:18.049       build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.049       copying pandas/tests/test_take.py ->
18:33:18.049       build/lib.linux-x86_64-cpython-314/pandas/tests
18:33:18.049       creating build/lib.linux-x86_64-cpython-314/pandas/tseries
18:33:18.049       copying pandas/tseries/__init__.py ->
18:33:18.049       build/lib.linux-x86_64-cpython-314/pandas/tseries
18:33:18.050       copying pandas/tseries/api.py ->
18:33:18.050       build/lib.linux-x86_64-cpython-314/pandas/tseries
18:33:18.050       copying pandas/tseries/frequencies.py ->
18:33:18.050       build/lib.linux-x86_64-cpython-314/pandas/tseries
18:33:18.050       copying pandas/tseries/holiday.py ->
18:33:18.050       build/lib.linux-x86_64-cpython-314/pandas/tseries
18:33:18.050       copying pandas/tseries/offsets.py ->
18:33:18.051       build/lib.linux-x86_64-cpython-314/pandas/tseries
18:33:18.051       creating build/lib.linux-x86_64-cpython-314/pandas/util
18:33:18.051       copying pandas/util/__init__.py ->
18:33:18.051       build/lib.linux-x86_64-cpython-314/pandas/util
18:33:18.051       copying pandas/util/_decorators.py ->
18:33:18.051       build/lib.linux-x86_64-cpython-314/pandas/util
18:33:18.051       copying pandas/util/_doctools.py ->
18:33:18.052       build/lib.linux-x86_64-cpython-314/pandas/util
18:33:18.052       copying pandas/util/_exceptions.py ->
18:33:18.052       build/lib.linux-x86_64-cpython-314/pandas/util
18:33:18.052       copying pandas/util/_print_versions.py ->
18:33:18.052       build/lib.linux-x86_64-cpython-314/pandas/util
18:33:18.052       copying pandas/util/_str_methods.py ->
18:33:18.052       build/lib.linux-x86_64-cpython-314/pandas/util
18:33:18.052       copying pandas/util/_test_decorators.py ->
18:33:18.053       build/lib.linux-x86_64-cpython-314/pandas/util
18:33:18.053       copying pandas/util/_tester.py ->
18:33:18.053       build/lib.linux-x86_64-cpython-314/pandas/util
18:33:18.053       copying pandas/util/_validators.py ->
18:33:18.053       build/lib.linux-x86_64-cpython-314/pandas/util
18:33:18.053       creating build/lib.linux-x86_64-cpython-314/pandas/_libs/tslibs
18:33:18.053       copying pandas/_libs/tslibs/__init__.py ->
18:33:18.053       build/lib.linux-x86_64-cpython-314/pandas/_libs/tslibs
18:33:18.053       creating build/lib.linux-x86_64-cpython-314/pandas/_libs/window
18:33:18.053       copying pandas/_libs/window/__init__.py ->
18:33:18.054       build/lib.linux-x86_64-cpython-314/pandas/_libs/window
18:33:18.054       creating build/lib.linux-x86_64-cpython-314/pandas/api/extensions
18:33:18.054       copying pandas/api/extensions/__init__.py ->
18:33:18.054       build/lib.linux-x86_64-cpython-314/pandas/api/extensions
18:33:18.054       creating build/lib.linux-x86_64-cpython-314/pandas/api/indexers
18:33:18.054       copying pandas/api/indexers/__init__.py ->
18:33:18.054       build/lib.linux-x86_64-cpython-314/pandas/api/indexers
18:33:18.054       creating build/lib.linux-x86_64-cpython-314/pandas/api/interchange
18:33:18.054       copying pandas/api/interchange/__init__.py ->
18:33:18.054       build/lib.linux-x86_64-cpython-314/pandas/api/interchange
18:33:18.055       creating build/lib.linux-x86_64-cpython-314/pandas/api/types
18:33:18.055       copying pandas/api/types/__init__.py ->
18:33:18.055       build/lib.linux-x86_64-cpython-314/pandas/api/types
18:33:18.055       creating build/lib.linux-x86_64-cpython-314/pandas/compat/numpy
18:33:18.055       copying pandas/compat/numpy/__init__.py ->
18:33:18.055       build/lib.linux-x86_64-cpython-314/pandas/compat/numpy
18:33:18.055       copying pandas/compat/numpy/function.py ->
18:33:18.055       build/lib.linux-x86_64-cpython-314/pandas/compat/numpy
18:33:18.055       creating build/lib.linux-x86_64-cpython-314/pandas/core/_numba
18:33:18.055       copying pandas/core/_numba/__init__.py ->
18:33:18.055       build/lib.linux-x86_64-cpython-314/pandas/core/_numba
18:33:18.055       copying pandas/core/_numba/executor.py ->
18:33:18.056       build/lib.linux-x86_64-cpython-314/pandas/core/_numba
18:33:18.056       creating build/lib.linux-x86_64-cpython-314/pandas/core/array_algos
18:33:18.056       copying pandas/core/array_algos/__init__.py ->
18:33:18.056       build/lib.linux-x86_64-cpython-314/pandas/core/array_algos
18:33:18.056       copying pandas/core/array_algos/datetimelike_accumulations.py ->
18:33:18.056       build/lib.linux-x86_64-cpython-314/pandas/core/array_algos
18:33:18.056       copying pandas/core/array_algos/masked_accumulations.py ->
18:33:18.056       build/lib.linux-x86_64-cpython-314/pandas/core/array_algos
18:33:18.056       copying pandas/core/array_algos/masked_reductions.py ->
18:33:18.056       build/lib.linux-x86_64-cpython-314/pandas/core/array_algos
18:33:18.056       copying pandas/core/array_algos/putmask.py ->
18:33:18.057       build/lib.linux-x86_64-cpython-314/pandas/core/array_algos
18:33:18.057       copying pandas/core/array_algos/quantile.py ->
18:33:18.057       build/lib.linux-x86_64-cpython-314/pandas/core/array_algos
18:33:18.057       copying pandas/core/array_algos/replace.py ->
18:33:18.057       build/lib.linux-x86_64-cpython-314/pandas/core/array_algos
18:33:18.057       copying pandas/core/array_algos/take.py ->
18:33:18.057       build/lib.linux-x86_64-cpython-314/pandas/core/array_algos
18:33:18.057       copying pandas/core/array_algos/transforms.py ->
18:33:18.057       build/lib.linux-x86_64-cpython-314/pandas/core/array_algos
18:33:18.057       creating build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.057       copying pandas/core/arrays/__init__.py ->
18:33:18.057       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.058       copying pandas/core/arrays/_mixins.py ->
18:33:18.058       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.058       copying pandas/core/arrays/_ranges.py ->
18:33:18.058       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.058       copying pandas/core/arrays/base.py ->
18:33:18.058       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.059       copying pandas/core/arrays/boolean.py ->
18:33:18.059       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.059       copying pandas/core/arrays/categorical.py ->
18:33:18.059       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.059       copying pandas/core/arrays/datetimelike.py ->
18:33:18.059       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.059       copying pandas/core/arrays/datetimes.py ->
18:33:18.059       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.060       copying pandas/core/arrays/floating.py ->
18:33:18.060       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.060       copying pandas/core/arrays/integer.py ->
18:33:18.060       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.060       copying pandas/core/arrays/interval.py ->
18:33:18.060       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.060       copying pandas/core/arrays/masked.py ->
18:33:18.060       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.060       copying pandas/core/arrays/numeric.py ->
18:33:18.060       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.060       copying pandas/core/arrays/numpy_.py ->
18:33:18.060       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.060       copying pandas/core/arrays/period.py ->
18:33:18.060       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.061       copying pandas/core/arrays/string_.py ->
18:33:18.061       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.061       copying pandas/core/arrays/string_arrow.py ->
18:33:18.061       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.061       copying pandas/core/arrays/timedeltas.py ->
18:33:18.061       build/lib.linux-x86_64-cpython-314/pandas/core/arrays
18:33:18.061       creating build/lib.linux-x86_64-cpython-314/pandas/core/computation
18:33:18.061       copying pandas/core/computation/__init__.py ->
18:33:18.061       build/lib.linux-x86_64-cpython-314/pandas/core/computation
18:33:18.061       copying pandas/core/computation/align.py ->
18:33:18.061       build/lib.linux-x86_64-cpython-314/pandas/core/computation
18:33:18.061       copying pandas/core/computation/api.py ->
18:33:18.061       build/lib.linux-x86_64-cpython-314/pandas/core/computation
18:33:18.062       copying pandas/core/computation/check.py ->
18:33:18.062       build/lib.linux-x86_64-cpython-314/pandas/core/computation
18:33:18.062       copying pandas/core/computation/common.py ->
18:33:18.062       build/lib.linux-x86_64-cpython-314/pandas/core/computation
18:33:18.062       copying pandas/core/computation/engines.py ->
18:33:18.062       build/lib.linux-x86_64-cpython-314/pandas/core/computation
18:33:18.062       copying pandas/core/computation/eval.py ->
18:33:18.062       build/lib.linux-x86_64-cpython-314/pandas/core/computation
18:33:18.062       copying pandas/core/computation/expr.py ->
18:33:18.062       build/lib.linux-x86_64-cpython-314/pandas/core/computation
18:33:18.062       copying pandas/core/computation/expressions.py ->
18:33:18.062       build/lib.linux-x86_64-cpython-314/pandas/core/computation
18:33:18.063       copying pandas/core/computation/ops.py ->
18:33:18.063       build/lib.linux-x86_64-cpython-314/pandas/core/computation
18:33:18.063       copying pandas/core/computation/parsing.py ->
18:33:18.063       build/lib.linux-x86_64-cpython-314/pandas/core/computation
18:33:18.063       copying pandas/core/computation/pytables.py ->
18:33:18.063       build/lib.linux-x86_64-cpython-314/pandas/core/computation
18:33:18.063       copying pandas/core/computation/scope.py ->
18:33:18.063       build/lib.linux-x86_64-cpython-314/pandas/core/computation
18:33:18.063       creating build/lib.linux-x86_64-cpython-314/pandas/core/dtypes
18:33:18.063       copying pandas/core/dtypes/__init__.py ->
18:33:18.063       build/lib.linux-x86_64-cpython-314/pandas/core/dtypes
18:33:18.063       copying pandas/core/dtypes/api.py ->
18:33:18.063       build/lib.linux-x86_64-cpython-314/pandas/core/dtypes
18:33:18.064       copying pandas/core/dtypes/astype.py ->
18:33:18.064       build/lib.linux-x86_64-cpython-314/pandas/core/dtypes
18:33:18.064       copying pandas/core/dtypes/base.py ->
18:33:18.064       build/lib.linux-x86_64-cpython-314/pandas/core/dtypes
18:33:18.064       copying pandas/core/dtypes/cast.py ->
18:33:18.064       build/lib.linux-x86_64-cpython-314/pandas/core/dtypes
18:33:18.064       copying pandas/core/dtypes/common.py ->
18:33:18.064       build/lib.linux-x86_64-cpython-314/pandas/core/dtypes
18:33:18.064       copying pandas/core/dtypes/concat.py ->
18:33:18.064       build/lib.linux-x86_64-cpython-314/pandas/core/dtypes
18:33:18.064       copying pandas/core/dtypes/dtypes.py ->
18:33:18.064       build/lib.linux-x86_64-cpython-314/pandas/core/dtypes
18:33:18.064       copying pandas/core/dtypes/generic.py ->
18:33:18.064       build/lib.linux-x86_64-cpython-314/pandas/core/dtypes
18:33:18.065       copying pandas/core/dtypes/inference.py ->
18:33:18.065       build/lib.linux-x86_64-cpython-314/pandas/core/dtypes
18:33:18.065       copying pandas/core/dtypes/missing.py ->
18:33:18.065       build/lib.linux-x86_64-cpython-314/pandas/core/dtypes
18:33:18.065       creating build/lib.linux-x86_64-cpython-314/pandas/core/groupby
18:33:18.065       copying pandas/core/groupby/__init__.py ->
18:33:18.065       build/lib.linux-x86_64-cpython-314/pandas/core/groupby
18:33:18.065       copying pandas/core/groupby/base.py ->
18:33:18.065       build/lib.linux-x86_64-cpython-314/pandas/core/groupby
18:33:18.065       copying pandas/core/groupby/categorical.py ->
18:33:18.065       build/lib.linux-x86_64-cpython-314/pandas/core/groupby
18:33:18.065       copying pandas/core/groupby/generic.py ->
18:33:18.065       build/lib.linux-x86_64-cpython-314/pandas/core/groupby
18:33:18.065       copying pandas/core/groupby/groupby.py ->
18:33:18.065       build/lib.linux-x86_64-cpython-314/pandas/core/groupby
18:33:18.065       copying pandas/core/groupby/grouper.py ->
18:33:18.066       build/lib.linux-x86_64-cpython-314/pandas/core/groupby
18:33:18.066       copying pandas/core/groupby/indexing.py ->
18:33:18.066       build/lib.linux-x86_64-cpython-314/pandas/core/groupby
18:33:18.066       copying pandas/core/groupby/numba_.py ->
18:33:18.066       build/lib.linux-x86_64-cpython-314/pandas/core/groupby
18:33:18.066       copying pandas/core/groupby/ops.py ->
18:33:18.066       build/lib.linux-x86_64-cpython-314/pandas/core/groupby
18:33:18.066       creating build/lib.linux-x86_64-cpython-314/pandas/core/indexers
18:33:18.066       copying pandas/core/indexers/__init__.py ->
18:33:18.066       build/lib.linux-x86_64-cpython-314/pandas/core/indexers
18:33:18.066       copying pandas/core/indexers/objects.py ->
18:33:18.066       build/lib.linux-x86_64-cpython-314/pandas/core/indexers
18:33:18.066       copying pandas/core/indexers/utils.py ->
18:33:18.066       build/lib.linux-x86_64-cpython-314/pandas/core/indexers
18:33:18.066       creating build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.067       copying pandas/core/indexes/__init__.py ->
18:33:18.067       build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.067       copying pandas/core/indexes/accessors.py ->
18:33:18.067       build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.067       copying pandas/core/indexes/api.py ->
18:33:18.067       build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.067       copying pandas/core/indexes/base.py ->
18:33:18.067       build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.067       copying pandas/core/indexes/category.py ->
18:33:18.067       build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.067       copying pandas/core/indexes/datetimelike.py ->
18:33:18.067       build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.067       copying pandas/core/indexes/datetimes.py ->
18:33:18.067       build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.068       copying pandas/core/indexes/extension.py ->
18:33:18.068       build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.068       copying pandas/core/indexes/frozen.py ->
18:33:18.068       build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.068       copying pandas/core/indexes/interval.py ->
18:33:18.068       build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.068       copying pandas/core/indexes/multi.py ->
18:33:18.068       build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.068       copying pandas/core/indexes/period.py ->
18:33:18.068       build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.068       copying pandas/core/indexes/range.py ->
18:33:18.068       build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.068       copying pandas/core/indexes/timedeltas.py ->
18:33:18.068       build/lib.linux-x86_64-cpython-314/pandas/core/indexes
18:33:18.068       creating build/lib.linux-x86_64-cpython-314/pandas/core/interchange
18:33:18.069       copying pandas/core/interchange/__init__.py ->
18:33:18.069       build/lib.linux-x86_64-cpython-314/pandas/core/interchange
18:33:18.069       copying pandas/core/interchange/buffer.py ->
18:33:18.069       build/lib.linux-x86_64-cpython-314/pandas/core/interchange
18:33:18.069       copying pandas/core/interchange/column.py ->
18:33:18.069       build/lib.linux-x86_64-cpython-314/pandas/core/interchange
18:33:18.069       copying pandas/core/interchange/dataframe.py ->
18:33:18.069       build/lib.linux-x86_64-cpython-314/pandas/core/interchange
18:33:18.069       copying pandas/core/interchange/dataframe_protocol.py ->
18:33:18.069       build/lib.linux-x86_64-cpython-314/pandas/core/interchange
18:33:18.069       copying pandas/core/interchange/from_dataframe.py ->
18:33:18.069       build/lib.linux-x86_64-cpython-314/pandas/core/interchange
18:33:18.069       copying pandas/core/interchange/utils.py ->
18:33:18.069       build/lib.linux-x86_64-cpython-314/pandas/core/interchange
18:33:18.069       creating build/lib.linux-x86_64-cpython-314/pandas/core/internals
18:33:18.069       copying pandas/core/internals/__init__.py ->
18:33:18.070       build/lib.linux-x86_64-cpython-314/pandas/core/internals
18:33:18.070       copying pandas/core/internals/api.py ->
18:33:18.070       build/lib.linux-x86_64-cpython-314/pandas/core/internals
18:33:18.070       copying pandas/core/internals/array_manager.py ->
18:33:18.070       build/lib.linux-x86_64-cpython-314/pandas/core/internals
18:33:18.071       copying pandas/core/internals/base.py ->
18:33:18.071       build/lib.linux-x86_64-cpython-314/pandas/core/internals
18:33:18.071       copying pandas/core/internals/blocks.py ->
18:33:18.071       build/lib.linux-x86_64-cpython-314/pandas/core/internals