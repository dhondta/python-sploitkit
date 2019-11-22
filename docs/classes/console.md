A *console* is a Read-Eval-Process-Loop (REPL) environment that holds a set of enabled commands, always starting from a root console. Each child console becomes bound to its parent when started so that it can also use its configuration settings.

## Components

Basically, a console holds the central logic of the CLI through multiple components :

- *Files Manager* : It manages files from the *WORKSPACE* (depending on the context, that is, the root level or another one setting the workspace elsewhere, e.g. as for a project).
- *Global State* : It holds the key-values to be shared amongst the console levels and modules and their associated commands.
- *Datastore* : It aims to persistently save data.
- *Jobs Pool* : It manages jobs to be run from the console.
- *Sessions Pool* : It manages the open sessions, obtained from the execution of *modules*.

In order to make a custom console, two classes exist :

- The generic `Console` class : for making child console levels.
- The specific `FrameworkConsole` class : to be used directly or subclassed to define the root console.

??? example "**Example**: Basic application running a `FrameworkConsole`"

        :::python
        from sploitkit import FrameworkConsole
        
        if __name__ == '__main__':
            FrameworkConsole("MySploit").start()

<br>

## Scope and prompt

A console can be tuned in the following way using some class attributes :

- `level` : the console level name, for use with *commands*
- `message` : a list of tokens with their styling, as of [`prompt_toolkit`](https://python-prompt-toolkit.readthedocs.io/en/master/pages/asking_for_input.html#coloring-the-prompt-itself)
- `style` : the style definition as a dictionary for the prompt tokens

??? example "**Example**: A console subclass for defining a new level"

        :::python
        from sploitkit import Console
        
        class MyConsole(Console):
            level = "new_level"
            message = [
                ('class:prompt', "["),
                ('class:name', None),
                ('class:prompt', "]"),
            ]
            style = {
                'prompt': "#eeeeee",
                'name':   "#ff0000",
            }
        
        
    <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAALIAAAAbCAIAAABX+0IZAAAAA3NCSVQICAjb4U/gAAAAEHRFWHRTb2Z0d2FyZQBTaHV0dGVyY4LQCQAADAFJREFUaN7tWnl4FFUSr/e6p+fIZCbJkIuEABKURUEEkQAuigfLp6iLH+IqihweeKALuCIBFARBw7dRQF0URC4RAivBgBxCNEEgRkIkkEBCJMfknsw9093Tx3v7RzjCPdkvHGLqm3+6p/p1ddWvflX1upHH7UromABXVwihhBBok+tV2CD1oqJidDpd8zMej9vlcl5T4xmdKUyvelx+mbZFslUFB6mn1WrPOWMymc3msGtpO2L0JrNRy7ToeTW6ED2HUVvkW4UtLihmc9g5yJAkqa6upnUpwRgVHxnCIgSUEqLIAcHrdnkE5f8iCKQ1R0dzLmutdMOWsOXLv7rYX+PGjb0asDhfOI5DgCi0IqkjzDAQcNY5eIIwo9GFmi0xeq6+upFvqxzXCVtUVVVem1ZRlUVRJAAg8LyE4mNNoXo7zwMAsMao+FCWxVSVeLe90SOqFAAQqzdbIkwGjgFV4j0Ou/sMvSCdJaGzBQCov6G83kcuroy1JovFbNSyiBKZd9TZvH+WJqYFsGgCREJCp2CUKyvLr+AYAwid6g6I7HO6BRU0hrCIiKgIucrGE6wLj40xUZ+zwSEBZ4wIj4lBNdXOQFNMqeSua/AqAEAUCnBRZcSZIy0hirOhVlCA0WBF+fPQU7AtJ0KIEIIx0wr3jByf1uDxen1er8+5+jF9ULcHhBDGrOn+hXtP/LZlXIwsnowRCfB+XhB4j10I6zZ46ID2CGGD2aSRXA2Nbr8g+N2N9nYv7znR6PV6fV5PQ/Hc2zWKLEuSJEkKoecp17skzmwOwQDAMBhUWRTEQEDkfbx0ZVBBYaPP7/X5vT6/Uwzog7+Qe2hxhbfJjV5n7pw78DWARRNbYNwa97Z/O2VQUr+kYfMPqMGC0hDVsfNNnTp1iuvZp5MpPDY2NHBe6uLEse+nTh7RCQOn5ZAiiqcIn8qKQtjjHz/erUti11sHflAYOMu55yqLooK0Wg0CKnrcAjbFdoiNDDdqmSs1vCCYZDD0M+jnMy30rbQr+c7ExMQuXR/59Kjayka1qIiorQML4rQecxCI7ecPOqNER51dIEDI4mEDfkpQiwt8Le5O/M76+npVr3KxXLB3ldx1Vl4fajKb28WZTY7aOlfgSjRWVowAUD9oKfAkr63eC4Cj+FYvbyfDjG5/Y+2+ksramtL9GxYuWPNTcVXFoYx5D7bDABD+9AqrPXNiHD7JFvqe7+Ud+vbZOxgKAMTQY+j0lRszfzlw8MAve37YtnrCgyEqAACy3DMjPTOvtKLObqs9cXDrJ2/cHRlUBWLjB7+5KrOwxmarKspcNvW+GBYAVCVgeubraofDWXU4e1/B52eXHs0984s87szxXbmuo7a5PbaKooIjJYvuO7nTgjQsi4FSmQIApRRws7yMEbzTy6x7HX6Hz2/18/+ViVHHUikgUxgsyZl+X42tZk9ZybN1nhCzSYsAAAZL8i5eKPPzDp+/hBdmq6rmdOZTeCYg5fp5u89f7+cLBGFos4ANluRMP2/z+YsEYaqqBpmRfWU5nResPr+VF5bJcrur2XKimJ5JN5UuHTEz95Ela0bbPxk1YuHwzz//4LWMH2ftd+3enkMe69evIxwrxJgyPe7sxYq5vxapCEDT5ZXPPrw/b2XKy7MrA2CM7hjv+13AAAAopEv/QT3tC8dO3u3QdOg/NnnahvToxx9I3i9c0h7TgLkZac8J6XNemnuM7fbU9HfSNnUc//SCHADHhteT9hiZqMf/kzH1nIvk3NRhd668I3nj0r4Fr46YlUe15kgLrTWbQrwycMYoHaMSVSUAQOWARE0hYSbRIyE2knd/73MyeuPauJgjgiAHSFRoeCgnuRv5JEnaICvbQo0pAF0D8gxbVTdd5DgAAEhU1b4Ixmu1jQD9ZPltQbSHGBYhBAB9ZGmxoqRqtdswwpQmEnr8FAUMkKQ0SU7XcnMx7iYr7whipF73JnOZTLlDkjNkeS3HfcBgi6rODUhfAhquYcnVgQUAINpQcjBvpz7fM1p/PDdnM+z7cMTNiSGw323btSWHT3ngwZgvj1ZiEpeU1N6Zn3M0AAiADYswgev4wV/yDjsRQOHhXIDmZFhzcFfWzwLA3qwisuvHtyY9tjBnXf0lGC925OQxHYtT7nr5s1IFIDO7mLt5/7sv3rvml3UVqrum1A3YV8+fT7aC7USJ3eKWqOSxlpSUqIBK9WGWiLCoGAZUSRJ9PpWcqiWORl1kRHh0CBB5QnGDhWH6M0w96COiLCcH1Lo6t6hOluRjBnNyXDzLMsVU1ZeWTqt1WLTapq06gvBWhhEAsjAeqPB/U9TFGpYCWAhFCO1jmAMIACD3dNApnSzJxRz3skajAGQyDCeQ6ZL8bz1Te6kqRt+W5SwtN4VlKQBgzKhkpaLEaVjrVZ5EEKEUEMJN82hTL0Eat6b9KN/16MPxoSFGXZ+7eknZmblNbhbyv5ifhsYu/D5j1fsTRg1sb8IAAKp6XgskF+3OqmZ79r7tktTJdO/Ti6vc+3OZ0nSsHM/eY4Wb/2JweMmFar+z6oTVcWomoTyl1Nl0RBXBWV9dWVZWVlZZXS8q9DQUqextrKkoLztRUV7ZWyG/smwFnKXsEhRMSC+AvSBZreVlZb+XlZfvIgQUtfv5JiBUjlA4pU1+zOS4dQDf8vx2MfCCqppOP1fTgiyjnDqTzTAsIbdeen+XkN6UDhEDNp+/0edv9Pm/UhRMaftrMKBSVVUJPSeh7Rlrd4hdhw3trrP0HnCbNi/zJ++pRChfN/eJoX+ftiEHDxqVumX7stH9QyW7vfECcxg5ibfLNeYXmuGaJRC9RHK1tPcFICh4My7SyzZTljGaYNAP1GpzACYJ4iFBHERbvOA5ZqzV6QYYDE2//gZDX72u4OpvZ5HMV26JPw8v1LVz6Tel6U8O7lhm6u39YUZ6XoWrWQzKrScOZK2aMzPxjfU/zZxw34oNhcK5eMOdkvrHkaNHzoxSVApIFEKMRgTCqbXUorx86cmBd3dmc0sVAGC7DvprvHI4v1A+Uy8EkYI5LKzZVSdFFEQUajIF63+K0EGEnlOUDixbeU6kMc4HGKioLIeb8nuQqioYFwa38hGWOcIy8wi3gefnKPJgjSaYBQMAQKkRQDjbjLsIsbKMcH3uciq5Xyz97bnkxXMA73xr52lM6JMmfjiE35V92OqU9dF9e7XXCNV23+l44X7jZ7zAZp9Q4x+dOq13bfro9GpyBmolxbVozPNTn7LtcFs6w8HlW4uV2vWpK17b/K/VS6QP1heztzyZ/Patx1cO31R7pgZ4CwvK6KvPTx/d8F1j+E1M/rLvjjY5mpQfLvRGD5ucnM1kN7Dtu2kPLU0vUi75UJ9quRFiYJsofsKyxxBiKXQGWM4yCkKpnGazJC1BsB7jW2TlbZWs1OtqL+elAbI8BFAWxk4EMaoaB2BFiAJAEAuWMBjJylRF2QHotBkpnGaLJG2mdBnLNABEEeJh2e0IXS+wAFK65qP019c+wa1etfX0VxYohOHCB4z5+MUOYToQXNbCvaljZqY5zgRRMvd66aNxCTqhfN/GV8e+s83dLMPlvIWTUrunjF+4foxYXbBiYtr3xS7q3Tdj2Ejnh7Ne+3xdO2Ir3LnoH8kpe5rvbyhHPvnnvB4fvbpg7VOB6oKVE9dlHD0JUt+WuROXRM9+ftH6KYyv8revXv9mc5HrknWlmmXv16OpkjwpIEVRKiB0SMNuBMYBsI/jRgKaJcnrKLVhvEivS2EuP18zFO5W5AmE6ABcGO/huOlN3WIQC+ZpNKkqGS8GxiBUoGHTgHEB/MpxDyGcLMupshwCUIvxpwwDVx4WqAVfZ3WZsi1reM7D98w+FMSmGk4Yl/Fbiu25DmMyhAu91riKr9zY22b+mjV07b2DFhxW4cYT3OPdnzMf3j0kaWY+gav3Yj20S69EA5j6jHpvUsKmsc8W/DFdyxojoqOjVUoFd4MncEPggQuNDDdgQBYD29r0cXlY4J4vLlk3vrNalb/pzZHJPzT+MV8j4u5TthRPAaDer4d3nrDrRsAF98C8A+vHRCAAAKVoxzUrIq0nbZ/4Xu9Z1OaCNmmDRZu0waJN2mDRJm2waJMrK/8DUa1LmmY8X7UAAAAASUVORK5CYII=" alt="Prompt rendered" />
<br>

## Entity sources

Another important attribute of the `Console` class is `sources`. It is only handled for the parent console and is defined as a dictionary with three possible keys :

- `banners` (default: `None`) : for customizing the startup application banner
- `entities` : a list of source folders to be parsed for importing entities
- `libraries` (default: "`.`") : a list of source folders to be added to `sys.path`

??? example "**Example**: Defining sources for banners, entities and libraries"

        :::python
        from sploitkit import FrameworkConsole

        class MyConsole(Console):
            ...
            sources = {
                'banners':   "banners",
                'libraries': "lib",
            }

<br>
