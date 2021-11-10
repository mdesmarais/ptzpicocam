import os

from setuptools import setup

deps = []
requirements_path = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'requirements.txt')
with open(requirements_path, 'r') as f:
    for line in f:
        if len(line.strip()) > 0:
            deps.append(line.strip())


setup(
    name='ptzpicocam',
    description='Simlation of a ptz camera',
    author='Sylvain Courty, Maxime Desmarais',
    author_email='sylvain.courty@apside-groupe.com, maxime.desmarais@apside-groupe.com',
    packages=['ptzpicocam', 'ptzsimcam'],
    package_data={
        'ptzsimcam': ['*.urdf']
    },
    install_requires=deps,
    extra_require={
        'docs': ['sphinx', 'sphinx-autoapi']
    },
    scripts=['scripts/ptzsim']
)
