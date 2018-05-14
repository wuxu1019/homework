
from RepoOps import RepoOps


RELEASE_PREFIX = 'release-'

def main():

    repo = RepoOps("296c7a34ddd69ac7b723037d805675821841bfb7")
    #repo.getOrgRepo('SlackRecruiting', 'br-code-exercise-73939156')
    repo.getUserRepo('homework')

    rls_branch = repo.getReleaseNameInfo()[0]
    print(rls_branch)
    repo.createReleaseBranch(RELEASE_PREFIX + rls_branch)
    next_rls_branch, next_rls_ver = repo.getNextReleaseInfo(rls_branch)
    print(next_rls_branch, next_rls_ver)

    last_rls_branch, last_rls_ver = repo.getLastReleaseInfo(rls_branch)

    repo.changePlist(next_rls_branch, next_rls_ver, rls_branch)
    if last_rls_branch:
        repo.generateFeatureReport(RELEASE_PREFIX+last_rls_branch, RELEASE_PREFIX+rls_branch)
    else:
        repo.generateFeatureReport(None, RELEASE_PREFIX + rls_branch)


if __name__ == '__main__':
    main()












