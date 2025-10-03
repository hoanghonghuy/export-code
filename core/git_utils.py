import git
import logging
import os

def _get_repo(t, path):
    """Tìm đối tượng repo Git từ đường dẫn, xử lý lỗi nếu không tìm thấy."""
    try:
        return git.Repo(path, search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        logging.error(t.get('error_git_repo_not_found', path=os.path.abspath(path)))
        return None
    except Exception as e:
        logging.error(f"{t.get('error_git_init_failed')}: {e}", exc_info=True)
        return None

def get_staged_files(t, repo_path):
    """Lấy danh sách các file đã được add vào staging area."""
    repo = _get_repo(t, repo_path)
    if not repo: return []
    
    repo_root = repo.working_tree_dir
    
    staged_files = [os.path.join(repo_root, item.a_path) for item in repo.index.diff('HEAD')]
    untracked_but_added = [os.path.join(repo_root, item.a_path) for item in repo.index.diff(None) if item.change_type == 'A']
    
    all_files = sorted(list(set(staged_files + untracked_but_added)))
    
    logging.info(t.get('info_git_found_staged', count=len(all_files)))
    logging.debug(f"Files in staging: {all_files}")
    return all_files

def get_changed_files_since(t, repo_path, branch):
    """Lấy danh sách các file đã thay đổi so với một nhánh cụ thể."""
    repo = _get_repo(t, repo_path)
    if not repo: return []
        
    try:
        diff_items = repo.head.commit.diff(branch)
        repo_root = repo.working_tree_dir
        changed_files = sorted([os.path.join(repo_root, item.a_path) for item in diff_items])
        
        logging.info(t.get('info_git_found_since', count=len(changed_files), branch=branch))
        logging.debug(f"Changed files: {changed_files}")
        return changed_files
    except git.exc.GitCommandError:
        logging.error(t.get('error_branch_not_found', branch=branch))
        return []
    except Exception as e:
        logging.error(t.get('error_diff_failed', branch=branch, error=e), exc_info=True)
        return []