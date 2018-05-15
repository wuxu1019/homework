from github import Github
import xml.etree.ElementTree as ET


# key file names
PLIST_INFO_FILE = 'release.plist'
RELEASE_INFO_FILE = 'releng/release_info.csv'
FEATURE_FLAG_FILE = 'featureflags/FF.csv'

# tag in plist
RELEASE_NAME_TAG = 'SLKReleaseName'
VERSION_TAG = 'CFBundleShortVersionString'

# msg formats
CODE_FREEZE_MSG = ' code freeze'
RELEASE_PREFIX = 'release-'

# feature flag report
FEATURE_REPORT = 'feature_flag_changes'
ON = 'ON'
OFF = 'OFF'

# email
RELEASE_TEAM_EMAIL = '******@slk.org.com'


class RepoOps(object):

    def __init__(self, token):
        """
        use [OAuth token] to init github
        :param token: [OAuth token]
        """
        self.git = Github(token)
        self.repo = None

    def get_user_repo(self, repo_name):
        """
        get user repo
        :param repo_name: repo name
        :return:
        """
        try:
            self.repo = self.git.get_user().get_repo(repo_name)
        except Exception as e:
            print("An exception was thrown on visit repo [{}]".format(
                repo_name))
            print(str(e))
            return False
        return True

    def get_org_repo(self, org_name, repo_name):
        """
        get organization repo
        :param org_name:
        :param repo_name:
        :return:
        """
        name = org_name+'/'+repo_name
        try:
            self.repo = self.git.get_repo(name, lazy=False)
        except Exception as e:
            print("An exception was thrown on visit repo [{}]".format(name))
            print(str(e))
            return False
        return True

    def get_release_name_info(self, branch='master'):
        """
        get release_name/ release_version from plist
        :param branch: branch to get release info
        :return: release_name, release_version
        """

        plist_data = self._get_content(PLIST_INFO_FILE, branch)['data_decode']
        try:
            plist_info = {}
            root = ET.fromstring(plist_data)
            plist_dict = root[0]
            for i in range(0, len(plist_dict), 2):
                if plist_dict[i+1].tag in ['true', 'false']:
                    plist_info[plist_dict[i].text] = plist_dict[i+1].tag
                else:
                    plist_info[plist_dict[i].text] = plist_dict[i+1].text
            print("In Plist, rls branch tag is: " +
                  "[{}], version tag is: [{}]".format(
                    plist_info[RELEASE_NAME_TAG],
                    plist_info[VERSION_TAG],))
            return [
                plist_info[RELEASE_NAME_TAG].lower(),
                plist_info[VERSION_TAG]
            ]
        except Exception as e:
            print("An exception was thrown on retrieve release branch name")
            print("Pls contact {0} for further support".format(
                RELEASE_TEAM_EMAIL))
            print(str(e))
            return [0, 0]

    def get_next_release_info(self, rls_branch, branch='master'):
        """
        get next_release_name/ next_release_version from release_info file
        :param rls_branch:
        :param branch:
        :return:
        """

        rls_data = self._get_content(RELEASE_INFO_FILE, branch)['data_decode']
        rls_data = rls_data.split('\n')
        i = -1
        for i in range(len(rls_data)):
            b, v = rls_data[i].lower().split(',')
            if rls_branch == b:
                break
        try:
            next_rls_name, next_rls_ver = rls_data[i+1].split(',')
            print('Next release tag is: [{}], release version is: [{}]'.format(
                next_rls_name,
                next_rls_ver,
            ))
            return [next_rls_name.lower(), next_rls_ver]
        except Exception as e:
            print("An exception was thrown on generate next release branch")
            print("Pls contact {0} for further support".format(
                RELEASE_TEAM_EMAIL))
            print(str(e))
            return [0, 0]

    def get_last_release_info(self, rls_branch, branch='master'):
        """
        get last_release_name/laset_release_version from release_info file
        :param rls_branch:
        :param branch:
        :return:
        """
        rls_data = self._get_content(RELEASE_INFO_FILE, branch)['data_decode']
        rls_data = rls_data.split('\n')
        i = -1
        for i in range(1, len(rls_data)):
            b, v = rls_data[i].lower().split(',')
            if rls_branch == b:
                break
        if i > 1:
            last_rls_name, last_rls_ver = rls_data[i-1].split(',')
            return [last_rls_name.lower(), last_rls_ver]
        else:
            return [0, 0]

    def create_release_branch(self, target_branch, src_branch='master'):
        """
        create release branch
        :param target_branch:
        :param src_branch:
        :return:
        """
        target_branch = RELEASE_PREFIX + target_branch
        rt = self._create_branch(target_branch.lower(), src_branch)
        if rt:
            print(
                "Release Branch: " +
                "{} create successfully with the URL as {}".format(
                    target_branch, rt.url))
            return True
        else:
            return False

    def change_plist(
            self, rls_name,
            rls_version, last_rls_name, branch='master'
    ):
        """
        change plist tags
        :param rls_name:
        :param rls_version:
        :param last_rls_name:
        :param branch:
        :return:
        """
        plist_content = self._get_content(PLIST_INFO_FILE, branch)
        declaration = '\n'.join(plist_content['data_decode'].split(
            '\n')[:2]) + '\n'

        root = ET.fromstring(plist_content['data_decode'])
        plist_dict = root[0]
        for i in range(0, len(plist_dict), 2):
            if plist_dict[i].text == VERSION_TAG:
                plist_dict[i+1].text = rls_version.upper()
            elif plist_dict[i].text == RELEASE_NAME_TAG:
                plist_dict[i+1].text = rls_name.upper()

        plist_modify = declaration.encode('utf-8') + ET.tostring(root)
        msg = RELEASE_PREFIX + last_rls_name.lower() + CODE_FREEZE_MSG
        sha = plist_content['sha']
        rt = self._update_file(PLIST_INFO_FILE, msg, plist_modify, sha)
        if rt:
            print("Plist Changed successfully with the URL as {0}".format(
                rt['content'].html_url))
            return True
        else:
            return False

    def generate_feature_report(self, last_rls, this_rls):
        """
        generate feature flag report
        :param last_rls: last release name
        :param this_rls: target release name
        :return:
        """

        this_rls = RELEASE_PREFIX + this_rls

        if last_rls:
            last_rls = RELEASE_PREFIX + last_rls
            ff_last = self._get_content(
                FEATURE_FLAG_FILE, last_rls)['data_decode']
            feature_last = self._count_feature(ff_last.split('\n'))
        else:
            last_rls = 'empty'
            feature_last = self._count_feature(None)

        ff_this = self._get_content(FEATURE_FLAG_FILE, this_rls)['data_decode']
        feature_this = self._count_feature(ff_this.split('\n'))

        # generate enabled/ disabled/ new/ delete features
        enabled = feature_this[ON] - feature_last[ON]
        disabled = feature_this[OFF] - feature_last[OFF]
        new = (feature_this[ON] | feature_this[
            OFF]) - feature_last[ON] - feature_last[OFF]
        delete = (feature_last[ON] | feature_last[
            OFF]) - feature_this[ON] - feature_this[OFF]
        report_name = '{2}_from_{0}_to_{1}.txt'.format(
            last_rls, this_rls, FEATURE_REPORT)

        # write report file
        try:
            with open(report_name, 'w') as fp:
                fp.write('='*60+'\n')
                fp.write('Feature flags change from {0} to {1}\n'.format(
                    last_rls, this_rls))
                fp.write('='*60 + '\n')

                fp.write('\nNew features are:\n')
                for f in sorted(list(new)):
                    fp.write(str(f)+'\n')
                fp.write('\nDelete features are:\n')
                for f in sorted(list(delete)):
                    fp.write(str(f)+'\n')
                fp.write('\nEnabled features are:\n')
                for f in sorted(list(enabled)):
                    fp.write(str(f)+'\n')
                fp.write('\nDisabled feature are:\n')
                for f in sorted(list(disabled)):
                    fp.write(str(f)+'\n')
            return True
        except Exception as e:
            print("An exception was thrown on feature flag report file write")
            print(str(e))
            return False

    def _count_feature(self, content):
        """
        used ct to record feature flags
        :param content:
        :return: ct
        """

        ct = {ON: set(), OFF: set()}
        if not content:
            return ct

        for line in content:
            if ',' in line:
                fname, flag = line.split(',')
                flag, fname = flag.strip().upper(), fname.strip().upper()
                ct[flag].add(fname)
        return ct

    def _get_content(self, file_name, branch):
        """
        get file content from repo
        :param file_name: file name
        :param branch: branch name
        :return: content dict
        """
        content = {}
        try:
            data = self.repo.get_file_contents(file_name, ref=branch)
            data_decode = data.decoded_content.decode('utf-8').lstrip('\n')
            content['data_decode'] = data_decode
            content['sha'] = data.sha
            return content
        except Exception as e:
            print("An exception was thrown on file [{0}] reading".format(
                file_name))
            print(str(e))
            return 0

    def _create_branch(self, target_branch, src_branch):
        """
        create target branch refs/heads based on src branch refs/heads
        :param target_branch:
        :param src_branch:
        :return: branch ref
        """
        try:
            src_b = self.repo.get_branch(src_branch)
            ref = self.repo.create_git_ref(
                ref='refs/heads/'+target_branch,
                sha=src_b.commit.sha)
            return ref
        except Exception as e:
            print("An exception was thrown on branch [{0}] creation".format(
                target_branch))
            print(str(e))
            return 0

    def _update_file(self, file, msg, content, sha):
        """
        update file in repo
        :param file: file name
        :param msg: commit msg
        :param content: file content
        :param sha: file's head sha
        :return:
        """
        try:
            rt = self.repo.update_file('/'+file, msg, content, sha)
            return rt
        except Exception as e:
            print("An exception was thrown on plist modify")
            print(str(e))
            return 0
