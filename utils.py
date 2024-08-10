# utils.py

import os

def get_user_files(user_id):
    result_dir = 'result'
    settings_dir = 'settings'
    viewed_dir = 'viewed'

    # Создаем папки, если их нет
    os.makedirs(f"{result_dir}/{user_id}", exist_ok=True)
    os.makedirs(f"{settings_dir}/{user_id}", exist_ok=True)
    os.makedirs(f"{viewed_dir}/{user_id}", exist_ok=True)

    return {
        'result': f"{result_dir}/{user_id}/result.csv",
        'settings': f"{settings_dir}/{user_id}/settings.json",
        'viewed': f"{viewed_dir}/{user_id}/viewed.txt"
    }

#база