from setuptools import setup

setup(
    name="homie",
    packages=["homie"],
    version="0.1.4",
    description="Experimental implementation of the IoT convention called homie",
    author="Jan Almeroth",
    author_email="homie-python@almeroth.com",
    url="https://github.com/jalmeroth/homie-python",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Home Automation"
    ],
    install_requires=['paho-mqtt>=1.2']
)
