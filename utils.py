import datetime
import json
import xmlrpclib

import pytz
import requests

import re
from subprocess import check_output, STDOUT


BASE_URL = 'http://pypi.python.org/pypi'


SESSION = requests.Session()


def req_rpc(method, *args):
    payload = xmlrpclib.dumps(args, method)

    response = SESSION.post(
        BASE_URL,
        data=payload,
        headers={'Content-Type': 'text/xml'},
    )
    if response.status_code == 200:
        result = xmlrpclib.loads(response.content)[0][0]
        return result
    else:
        # Some error occurred
        pass


def get_json_url(package_name):
    return BASE_URL + '/' + package_name + '/json'


safe_url_re = re.compile(
    '^https:\/\/pypi.python.org\/packages\/source\/[a-z0-9]\/[a-z0-9-_.]+\/[a-z0-9-_.]+$', re.I)

def annotate_pep8(packages):
    urls = get_source_package_urls(packages)
    num_packages = len(packages)
    good_packages = []
    print('Downloading and running pep8...')
    for index, package in enumerate(packages):
        print index + 1, num_packages, package['name']
        if not package['name'] in urls:
            print 'No url for package'.format(package['name'])
            continue
        pep8 = download_package_and_run_pep8(urls[package['name']])
        package['pep8'] = pep8['pep8']
        package['lines'] = pep8['lines']
        package['ratio'] = pep8['ratio']
        package['wheel'] = False
        package['generic_wheel'] = False

        # Display logic. I know, I'm sorry.
        package['value'] = 1
        if package['ratio'] < 0.005:
            package['css_class'] = 'success'
            package['color'] = '#47a447'
            package['icon'] = u'\u2713'  # Check mark
            package['title'] = 'This package has 0% pep8 errors!'
            package['generic_wheel'] = True
        elif package['ratio'] <= 0.05:
            package['css_class'] = 'warning'
            package['color'] = '#ed9c28'
            package['icon'] = u'\u2717'  # Ballot X
            package['title'] = 'This package has {:.0%} pep8 errors.'.format(package['ratio'])
            package['wheel'] = True
        else:
            package['css_class'] = 'danger'
            package['color'] = '#d2322d'
            package['icon'] = u'\u2717'  # Ballot X
            package['title'] = 'This package has {:.0%} pep8 errors!!'.format(package['ratio'])
        good_packages.append(package)

    packages = good_packages


def download_package_and_run_pep8(url):
    """Download a package and extract its contents to a temp directory.

    Needs to handle tar.bz2, tar.gz, tgz, and zip

    """
    if not safe_url_re.search(url):
        return None
    check_output('rm -rf ./temp', shell=True)
    check_output('mkdir temp', shell=True)
    check_output('cd temp; wget --no-check-certificate {0}'.format(url), stderr=STDOUT, shell=True)
    fname = url.rsplit('/', 1)
    check_output('cd temp; tar -xf {0}'.format(fname[-1]), shell=True)
    pep8 = check_output('find ./temp/ -name "*.py" -print0 | xargs -0 pep8 -qq --max-line-length=99 --count; exit 0', stderr=STDOUT, shell=True)
    pep8 = pep8.strip()
    print 'pep8', pep8
    lines = check_output('find ./temp/ -name "*.py" -print0 | xargs -0 egrep ".*" | wc -l', shell=True)
    lines = lines.strip()
    print 'lines', lines
    ratio = float(pep8) / int(lines)
    print 'ratio {:.2%}'.format(ratio)
    check_output('rm -rf ./temp', shell=True)
    return {'pep8': pep8, 'lines': lines, 'ratio': ratio}


def get_source_package_urls(packages):
    result = {}
    print('Getting source package data...')
    num_packages = len(packages)
    for index, package in enumerate(packages):
        print index + 1, num_packages, package['name']
        url = get_json_url(package['name'])
        response = SESSION.get(url)
        if response.status_code != 200:
            print(' ! Skipping ' + package['name'])
            continue
        data = response.json()
        for d in data['urls']:
            # ignore installer files, kludge to handle wierd django-lfs package
            if d['packagetype'] == 'sdist' and not d['url'].count('installer'):
                result[package['name']] = d['url']
                break

    return result

def annotate_wheels(packages):
    print('Getting wheel data...')
    num_packages = len(packages)
    for index, package in enumerate(packages):
        print index + 1, num_packages, package['name']
        generic_wheel = False
        has_wheel = False
        url = get_json_url(package['name'])
        response = SESSION.get(url)
        if response.status_code != 200:
            print(' ! Skipping ' + package['name'])
            continue
        data = response.json()
        for download in data['urls']:
            if download['packagetype'] == 'bdist_wheel':
                has_wheel = True
                generic_wheel = download['filename'].endswith('none-any.whl')
        package['wheel'] = has_wheel
        package['generic_wheel'] = generic_wheel

        # Display logic. I know, I'm sorry.
        package['value'] = 1
        if generic_wheel:
            package['css_class'] = 'success'
            package['color'] = '#47a447'
            package['icon'] = u'\u2713'  # Check mark
            package['title'] = 'This package provides a generic wheel that should work everywhere.'
        elif has_wheel:
            package['css_class'] = 'warning'
            package['color'] = '#ed9c28'
            package['icon'] = '?'
            package['title'] = 'This package only has platform or achitecture-specific builds.'
        else:
            package['css_class'] = 'danger'
            package['color'] = '#d2322d'
            package['icon'] = u'\u2717'  # Ballot X
            package['title'] = 'This package has no wheel archives uploaded (yet!).'


def get_top_packages():
    print('Getting packages...')
    packages = req_rpc('top_packages')
    return [{'name': n, 'downloads': d} for n, d in packages]


def remove_irrelevant_packages(packages, limit):
    print('Removing cruft...')
    return packages[:limit]


def save_to_file(packages, file_name):
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    with open(file_name, 'w') as f:
        f.write(json.dumps({
            'data': packages,
            'last_update': now.strftime('%A, %d %B %Y, %X %Z'),
        }))
