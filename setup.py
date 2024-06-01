import setuptools

setuptools.setup(
    name="hyperflow-viz-trace",
    version="1.3.1",
    description="Tool for visualization of HyperFlow execution traces",
    url="https://github.com/hyperflow-wms/hyperflow-viz-trace",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'hflow-viz-trace = hyperflow_viz_trace.main:main',
        ],
    },
    install_requires=[
        'seaborn',
        'jsonlines',
        'pandas',
        'natsort',
        'scipy',
        'matplotlib==3.4.0'
    ]
)
