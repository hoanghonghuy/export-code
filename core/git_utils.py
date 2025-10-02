import git
import logging
import os

def _get_repo(path):
    """Tìm đối tượng repo Git từ đường dẫn, xử lý lỗi nếu không tìm thấy."""
    try:
        # search_parent_directories=True cho phép chạy tool từ thư mục con
        return git.Repo(path, search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        logging.error(f"❌ Lỗi: Thư mục '{os.path.abspath(path)}' không phải là một kho chứa Git.")
        return None
    except Exception as e:
        logging.error(f"❌ Đã xảy ra lỗi khi khởi tạo repo Git: {e}", exc_info=True)
        return None

def get_staged_files(repo_path):
    """Lấy danh sách các file đã được add vào staging area."""
    repo = _get_repo(repo_path)
    if not repo:
        return []
    
    repo_root = repo.working_tree_dir
    # Lấy diff giữa HEAD (commit cuối) và index (staging area)
    # Bao gồm các file mới (A), đã sửa (M), đổi tên (R)
    staged_files = [
        os.path.join(repo_root, item.a_path)
        for item in repo.index.diff('HEAD')
    ]
    
    # Lấy các file chưa được tracked nhưng đã được add
    untracked_but_added = [
        os.path.join(repo_root, item.a_path)
        for item in repo.index.diff(None) if item.change_type == 'A'
    ]
    
    all_files = sorted(list(set(staged_files + untracked_but_added)))
    logging.info(f"🔍 Tìm thấy {len(all_files)} file trong staging area.")
    logging.debug(f"Các file trong staging: {all_files}")
    return all_files

def get_changed_files_since(repo_path, branch):
    """Lấy danh sách các file đã thay đổi so với một nhánh cụ thể."""
    repo = _get_repo(repo_path)
    if not repo:
        return []
        
    try:
        # Lấy diff giữa commit hiện tại (HEAD) và commit của nhánh được chỉ định
        diff_items = repo.head.commit.diff(branch)
        
        repo_root = repo.working_tree_dir
        changed_files = sorted([
            os.path.join(repo_root, item.a_path) for item in diff_items
        ])
        
        logging.info(f"🔍 Tìm thấy {len(changed_files)} file đã thay đổi so với nhánh '{branch}'.")
        logging.debug(f"Các file đã thay đổi: {changed_files}")
        return changed_files
    except git.exc.GitCommandError:
        logging.error(f"❌ Lỗi: Không tìm thấy nhánh (branch) '{branch}'. Vui lòng kiểm tra lại tên nhánh.")
        return []
    except Exception as e:
        logging.error(f"❌ Đã xảy ra lỗi khi so sánh với nhánh '{branch}': {e}", exc_info=True)
        return []