from svg_lint import generate_svg_wheel
from utils import (
    annotate_pep8,
    get_top_packages,
    remove_irrelevant_packages,
    save_to_file,
)


TO_CHART = 360


def main():
    packages = remove_irrelevant_packages(get_top_packages(), TO_CHART)
    annotate_pep8(packages)
    save_to_file(packages, 'results.json')
    generate_svg_wheel(packages, TO_CHART)


if __name__ == '__main__':
    main()
