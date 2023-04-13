## Creating a project

Creating a project can be achieved by using the `sploitkit-new` tool like follows :

```sh
$ sploitkit-new --help
usage: sploitkit-new [-s] [-h] [-v] name

SploitkitNew

positional arguments:
  name             project name

optional arguments:
  -s, --show-todo  show the TODO list (default: False)

extra arguments:
  -h, --help       show this help message and exit
  -v, --verbose    verbose mode (default: False)

```

```sh
$ sploitkit-new -s my-sploit
12:34:56 [INFO] TODO list:
- [README:3] Fill in the README
- [main.py:MySploitConsole:6] set your console attributes
- [main.py:MySploitConsole:13] configure your console settings
- [commands/template.py:CommandWithOneArg:9] compute the list of possible values
- [commands/template.py:CommandWithOneArg:13] compute results here
- [commands/template.py:CommandWithOneArg:17] validate the input value
- [commands/template.py:CommandWithTwoArgs:27] compute the list of possible keys
- [commands/template.py:CommandWithTwoArgs:31] compute the list of possible values taking the key into account
- [commands/template.py:CommandWithTwoArgs:35] compute results here

```

This creates a folder `my-sploit` with the following items :

```sh
$ cd my-sploit/
$ ll
total 28K
drwxrwxr-x   5 user user 4.0K 2019-12-25 12:34 .
drwxr-xr-x 102 user user 4.0K 2019-12-25 12:34 ..
drwxrwxr-x   2 user user 4.0K 2019-12-25 12:34 banners
drwxrwxr-x   2 user user 4.0K 2019-12-25 12:34 commands
-rw-rw-r--   1 user user  279 2019-12-25 12:34 main.py
drwxrwxr-x   2 user user 4.0K 2019-12-25 12:34 modules
-rw-rw-r--   1 user user   31 2019-12-25 12:34 README
-rw-rw-r--   1 user user    0 2019-12-25 12:34 requirements.txt

```

-----

## Setting the root console

-----

## Adding commands


-----

## Adding modules


-----

## Tuning the datastore
