from setuptools import setup, find_packages

setup(
    name='ros2grapher',
    version='0.1.0',
    description='Visualize ROS2 node topology from source code — no robot required.',
    author='Supul',
    packages=find_packages(),
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'ros2grapher=ros2grapher.cli:main',
        ],
    },
)
