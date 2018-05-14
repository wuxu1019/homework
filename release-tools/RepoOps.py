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



class RepoOps(object):
    def __init__(self, token):
        self.git = Github(token)

    def getUserRepo(self, repo_name):
        try:
            self.repo = self.git.get_user().get_repo(repo_name)
        except Exception as e:
            print("An exception was thrown on visit repo [{}]".format(repo_name))
            print(str(e))
            exit(1)

    def getOrgRepo(self, org_name, repo_name):
        name = org_name+'/'+repo_name
        try:
            self.repo = self.git.get_repo(name, lazy=False)
        except Exception as e:
            print("An exception was thrown on visit repo [{}]".format(name))
            print(str(e))
            exit(1)

    def getReleaseNameInfo(self, branch='master'):

        plist_data = self._getContent(PLIST_INFO_FILE, branch)['data_decode']
        plist_info = {}
        root = ET.fromstring(plist_data)
        plist_dict = root[0]
        for i in range(0, len(plist_dict), 2):
            if plist_dict[i+1].tag in ['true', 'false']:
                plist_info[plist_dict[i].text] = plist_dict[i+1].tag
            else:
                plist_info[plist_dict[i].text] = plist_dict[i+1].text

        return plist_info[RELEASE_NAME_TAG].lower(), plist_info[VERSION_TAG]

    def getNextReleaseInfo(self, rls_branch, branch='master'):

        rls_data = self._getContent(RELEASE_INFO_FILE, branch)['data_decode']
        rls_data = rls_data.split('\n')
        for i in range(len(rls_data)):
            if rls_branch in rls_data[i].lower():
                break
        if i < len(rls_data) - 1:
            next_rls_name, next_rls_ver = rls_data[i+1].split(',')
            return next_rls_name.lower(), next_rls_ver
        else:
            raise Exception('release branch used out')
            exit(3)

    def getLastReleaseInfo(self, rls_branch, branch='master'):
        rls_data = self._getContent(RELEASE_INFO_FILE, branch)['data_decode']
        rls_data = rls_data.split('\n')
        for i in range(len(rls_data)):
            if rls_branch in rls_data[i].lower():
                break
        if i > 0:
            last_rls_name, last_rls_ver = rls_data[i-1].split(',')
            return last_rls_name.lower(), last_rls_ver
        else:
            return None, None



    def createReleaseBranch(self, target_branch, src_branch='master'):

        try:
            target_branch = target_branch.lower()
            src_b = self.repo.get_branch(src_branch)
            ref = self.repo.create_git_ref(ref='refs/heads/'+target_branch, sha=src_b.commit.sha)
        except Exception as e:
            print("An exception was thrown on branch [{0}] creation".format(target_branch))
            print(str(e))
            exit(2)
        print("Release Branch: {} create successfully with the URL as {}".format(target_branch, ref.url))


    def changePlist(self, rls_name, rls_version, last_rls_name, branch='master'):
        plist_content = self._getContent(PLIST_INFO_FILE, branch)
        declaration = '\n'.join(plist_content['data_decode'].split('\n')[:2]) + '\n'

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
        self._updateFile(PLIST_INFO_FILE, msg, plist_modify, sha)

    def _updateFile(self, file, msg, content, sha):
        try:
            rt = self.repo.update_file('/'+file, msg, content, sha)
        except Exception as e:
            print("An exception was thrown on plist modify")
            print(str(e))
            exit(5)
        print("Plist change successfully")


    def generateFeatureReport(self, last_rls, this_rls):


        if last_rls:
            ff_last = self._getContent(FEATURE_FLAG_FILE, last_rls)['data_decode']
            feature_last = self.countFeature(ff_last.split('\n'))
        else:
            last_rls = 'empty'
            feature_last = self.countFeature(None)

        ff_this = self._getContent(FEATURE_FLAG_FILE, this_rls)['data_decode']
        feature_this = self.countFeature(ff_this.split('\n'))
        enabled = feature_this[ON] - feature_last[ON]
        disabled = feature_this[OFF] - feature_last[OFF]
        new = (feature_this[ON] | feature_this[OFF]) - feature_last[ON] - feature_last[OFF]
        delete = (feature_last[ON] | feature_last[OFF]) - feature_this[ON] - feature_this[OFF]
        report_name = '{2}_from_{0}_to_{1}.txt'.format(last_rls, this_rls, FEATURE_REPORT)
        with open(report_name, 'w') as fp:
            fp.write('='*60+'\n')
            fp.write('Feature flags change from {0} to {1}\n'.format(last_rls, this_rls))
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

    def countFeature(self, content):

        ct = {ON: set(), OFF: set()}
        if not content:
            return ct

        for line in content:
            if ',' in line:
                fname, flag = line.split(',')
                flag, fname = flag.strip().upper(), fname.strip().upper()
                ct[flag].add(fname)
        return ct

    def _getContent(self, file_name, branch):
        content = {}
        try:
            data = self.repo.get_file_contents(file_name, ref=branch)
            data_decode = data.decoded_content.decode('utf-8').lstrip('\n')
            content['data_decode'] = data_decode
            content['sha'] = data.sha
        except Exception as e:
            print("An exception was thrown on file [{0}] reading".format(file_name))
            print(str(e))
            exit(4)
        return content














