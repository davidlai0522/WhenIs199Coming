from setuptools import setup, find_packages

setup(
    name='bus_app',
    version='0.1.0',
    author='David Lai',
    author_email='davidlaienhan5906@gmail.com',
    description='A short description of your project',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        # List your project dependencies here.
        # For example: 'requests >= 2.19.1',
        'requests',
        'groq',
        'python-telegram-bot == 21.4',
    ],
)