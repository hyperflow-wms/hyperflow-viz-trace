import setuptools

setuptools.setup(
    name="hyperflow-viz-trace",
    version="1.4.0",
    description="Tool for fast, interactive visualization of HyperFlow execution traces",
    url="https://github.com/hyperflow-wms/hyperflow-viz-trace",
    author="HyperFlow WMS Team",
    author_email="your-email@example.com",  # replace or remove if not needed
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Visualization"
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'hflow-viz-trace = hyperflow_viz_trace.main:main',
        ],
    },
    install_requires=[
        'pandas>=1.1',
        'natsort',
        'matplotlib>=3.4,<4.0',
        'mplcursors>=0.5',
        'ipympl>=0.9'
    ],
    extras_require={
        "dev": ["black", "flake8"],
        "jupyter": ["notebook", "jupyterlab"]
    },
    include_package_data=True,
)