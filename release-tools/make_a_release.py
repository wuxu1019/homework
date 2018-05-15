from RepoOps import RepoOps

# org/repo name
ORG_NAME = 'SlackRecruiting'
REPO_NAME = 'br-code-exercise-73939156'


def main():

    token = input(
        "Pls input [OAuth token], " +
        "HELP: You can ref README.txt on how to get [OAuth token]\n")
    print("\n===== Start to make a release =====\n\n")

    # Step1: Repo authentication
    print("\n[Step1] Repo authentication")
    repo = RepoOps(token)
    if not repo.get_org_repo('SlackRecruiting', 'br-code-exercise-73939156'):
        print("[Step1] Repo authentication fail")
        exit(1)

    # Step2: Get release branch name
    print("\n[Step2] Get release branch name")
    rls_branch = repo.get_release_name_info()[0]
    if not rls_branch:
        print("[Step2] Get release branch name fail")
        exit(1)

    # Step3: Create release branch
    print("\n[Step3] Create release branch")
    if not repo.create_release_branch(rls_branch):
        print("[Step3] Create release branch fail")
        exit(1)

    # Step4: find next release branch name and version
    print("\n[Step4] find next release branch name and version")
    next_rls_branch, next_rls_ver = repo.get_next_release_info(rls_branch)
    if not next_rls_branch:
        print("[Step4] find next release branch fail")
        exit(1)

    # Step5: Change plist with next release branch name and version
    print("\n[Step5] Change plist with next release branch name and version")
    if not repo.change_plist(next_rls_branch, next_rls_ver, rls_branch):
        print("[Step5] Change plist fail")
        exit(1)

    # Step6: Generate feature flag report
    print("\n[Step6] Generate feature flag report")
    last_rls_branch, last_rls_ver = repo.get_last_release_info(rls_branch)
    if not repo.generate_feature_report(last_rls_branch, rls_branch):
        print("[Step6] Generate feature flag  fail")
        exit(1)

    print("\n===== Success on make a release =====")


if __name__ == '__main__':
    main()
