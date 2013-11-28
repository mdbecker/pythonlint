from svg_lint import generate_svg_wheel
from utils import (
    annotate_pep8,
    get_top_packages,
    remove_irrelevant_packages,
    save_to_file,
)


TO_CHART = 360


def main():
    packages = remove_irrelevant_packages(get_top_packages(), int(TO_CHART * 1.05))
    packages = annotate_pep8(packages)
    packages = remove_irrelevant_packages(packages, TO_CHART)
    save_to_file(packages, 'results.json')
    generate_svg_wheel(packages, len(packages))


if __name__ == '__main__':
    main()
