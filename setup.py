from setuptools import find_packages, setup

setup(
    name="brapi",
    description="Brian's API for Django",
    version="0.0.2",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["Django>=5.0", "Pydantic>=2.9.2"],
)
