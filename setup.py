from setuptools import setup

if __name__ == "__main__":
    setup(
        entry_points = {'console_scripts': ['image-shrink = image_shrink.main:main']}
    )
