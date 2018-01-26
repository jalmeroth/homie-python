from setuptools import setup
<<<<<<< HEAD

version = "0.3.0"
||||||| merged common ancestors

version = "0.2.1"
=======
exec(open('homie/version.py').read())
>>>>>>> dev

setup(
    name="homie",
    packages=["homie"],
<<<<<<< HEAD
    version=version,
    description="Experimental implementation of the IoT convention called homie 2",
||||||| merged common ancestors
    version=version,
    description="Experimental implementation of the IoT convention called homie",
=======
    version=__version__,
    description="Experimental implementation of the IoT convention called homie",
>>>>>>> dev
    author="Jan Almeroth",
    author_email="homie-python@almeroth.com",
    url="https://github.com/jalmeroth/homie-python",
    download_url="https://github.com/jalmeroth/homie-python/tarball/" + __version__,
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Home Automation"
    ],
    install_requires=[
        'paho-mqtt>=1.2',
        'netifaces>=0.10.6'
    ]
)
