
## Contributing and testing

We use the [pre-commit](https://pre-commit.com) framework to automatically lint for code
style and common pitfals.

Before you commit to your local copy of the repo, please run this from the top level
```shell
$ python -m pip install -u -e .
$ python -m pip install -r requirements/tests.txt
```

It is also recommended to install `pre-commit` on your machine and then run,
from the top level
```shell
$ pre-commit install
```

We use the [pytest](https://docs.pytest.org/en/latest/) framework to test `idfx`'s
internal components. The test suite can be run from the top level with a simple `pytest`
invocation.
```shell
$ pytest
```
