from setuptools import setup, find_packages
filepath = 'README.md'
setup(
        name="micropython-dcompy",
        version="1.3",
        description="dcom micropython package",
        long_description=open(filepath, encoding='utf-8').read(),
        long_description_content_type="text/markdown",
        author="jdh99",
        author_email="jdh821@163.com",
        url="https://github.com/jdhxyy/dcom-micropython",
        packages=find_packages(),
        data_files=[filepath]
    )
