from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def main(init_new=True):
    my_drive = get_auth_drive()
    dest_id = input("Nhập id đích: ")
    src_id = input("Nhập id nguồn: ")
    if init_new:
       dest_id = create_parent_folder(my_drive, dest_id, src_id)
    copy_from_folder(my_drive, src_id, dest_id)

def get_auth_drive():
    # load credentials.json của client settings.yaml
    gauth = GoogleAuth("settings.yaml")
    # Kiểm tra credentials
    if gauth.credentials is None:
        # Authenticate qua local
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh nếu token đã expired
        gauth.Refresh()
    else:
        # Nếu credentials.json hợp lệ => Authenticate
        gauth.Authorize()
    # Lưu credentials.json vào thực mục hiện tại 
    gauth.SaveCredentialsFile("credentials.json")
    drive = GoogleDrive(gauth)
    return drive

def copy_file(drive, source_id, parent_folder_id):
    # Tạo instance của file id trên
    source = drive.CreateFile({'id': source_id})
    source.FetchMetadata('title')

    # Copy của dữ liệu từ file gốc 
    service = drive.auth.service
    copied_file = {
        'title': source['title'], 
        'parents': [{'id': parent_folder_id}]
    }
    f = service.files().copy(
        fileId=source_id, 
        supportsAllDrives=True, 
        body=copied_file
    ).execute()
    print('title: %s, id: %s' % (f['title'], f['id']))

def copy_folder(drive, folder, parent_id):
    # Tạo instance từ folder id trên (được đính kìm với folder) 
    copy_folder = drive.CreateFile({
        'mimeType': 'application/vnd.google-apps.folder', 
        'title': folder['title'], 
        'parents': [{'id': parent_id}]
    })
    copy_folder.Upload()
    print(f'title: %s, id: %s' % (copy_folder['title'], copy_folder['id']))
    return copy_folder['id']

def copy_from_folder(drive, folder_id, parent_folder_id):
    # Copy dữ liệu từ folder_id vào parent folder 
    file_list = drive.ListFile({
        'corpora': "allDrives", 
        'q': "'%s' in parents and trashed = false" % (folder_id) 
    }).GetList()
    for file_c in file_list:
        if file_c['mimeType'] == 'application/vnd.google-apps.folder':
            # Kiểm tra xem file hiện tại có phải folder không => nếu là folder <=> đệ quy với subfolders
            copied_folder = copy_folder(drive, file_c, parent_folder_id)
            original_folder = file_c['id']
            copy_from_folder(drive, original_folder, copied_folder)
        else:
            # Nếu không thì copy file
            copy_file(drive, file_c['id'], parent_folder_id)

def create_parent_folder(drive, id, source_folder_id):
    # Tạo parent folder với name tương ứng 
    folder_source = drive.CreateFile({'id': source_folder_id})
    folder_source.FetchMetadata('title')
    print('title: %s, id: %s' % (folder_source['title'], folder_source['id']))
    
    # Thêm parent folder vào folder hiện tại   
    copied_folder = drive.CreateFile({
        'mimeType': 'application/vnd.google-apps.folder', 
        'title': folder_source['title'],
        'parents': [{'id': id}]
    })
    copied_folder.Upload()
    return copied_folder['id']

if __name__=='__main__':
    main()