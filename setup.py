from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pid_controller',
      version='0.1',
      description='Simple PID controller implementation',
      long_description=readme(),
      url='http://github.com/jrheling/pid_controller',
      author='Joshua Heling',
      author_email='jrh@netfluvia.org',
      license='BSD',
      packages=['pid_controller'],
      include_package_data=True,    ## causes non-python files in the MANIFEST to be included at install time
      zip_safe=False)