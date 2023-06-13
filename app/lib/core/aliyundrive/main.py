import threading
import time
from concurrent.futures import as_completed

from altfe.interface.cloud import interCloud
from app.lib.core.aliyundrive.aliyundrive import AliyunDrive


@interCloud.bind("cloud_aliyundrive", "LIB_CORE")
class CoreAliyunDrive(interCloud):
    def __init__(self):
        super().__init__()
        self.conf = self.INS.conf.dict("aliyundrive")
        self.api = {}
        self.listOutdated = 0
        self.rootPath = [x for x in self.conf["rootPath"].split("/") if x != ""]
        self.auto()

    def auto(self):
        if self.conf["accounts"] is None:
            return
        self.is_on = True
        _token = self.loadConfig(self.getENV("rootPathFrozen") + "app/config/.token/aliyundrive.json", default={})
        for u in self.conf["accounts"]:
            if u not in _token:
                print(f"[阿里云盘@{u}] 根据此网址「https://media.cooluc.com/decode_token/」的方法获取 Refresh Token 或 BizExt 以登录")
                _input = str(input(f"Refresh_Token or BizExt: ").strip())
                if len(_input) > 64:
                    rtCode = AliyunDrive.get_userinfo_via_bizext(_input)
                else:
                    rtCode = _input
            else:
                rtCode = _token[u]["refresh"]
            self.api[u] = AliyunDrive(rtCode)
            if not self.api[u].do_refresh_token():
                print(f"[AliyunDrive@{u}] 登录失败")
        self.__save_token()
        t = threading.Timer(0, self.__check)
        t.setDaemon(True)
        t.start()

    def __check(self):
        while True:
            tim = time.time()
            isUP = False
            for u in self.api:
                if tim > self.api[u].get_token("expire") - 600:
                    try:
                        self.api[u].do_refresh_token()
                    except Exception as e:
                        self.STATIC.localMsger.error(e)
                    else:
                        isUP = True
            if isUP:
                self.__save_token()
            if tim > self.listOutdated:
                self.load_list()
            time.sleep(self.conf["sys_checkTime"])

    def __save_token(self):
        r = {}
        for u in self.api:
            r[u] = self.api[u].get_token()
        self.STATIC.file.aout(self.getENV("rootPathFrozen") + "app/config/.token/aliyundrive.json", r)

    def load_list(self):
        if self.is_on is False:
            return False
        for u in self.conf["accounts"].copy():
            self.inCheck = True
            tmp = []
            try:
                self.__pro_load_list(u, tmp)
                psws = interCloud.process_add_password(tmp)
            except Exception as e:
                self.STATIC.localMsger.error(e)
            else:
                self.dirPassword[u] = psws
                self.list[u] = tuple(tmp)
                self.listOutdated = time.time() + self.conf["sys_dataExpiredTime"]
                print(f"[AliyunDrive] {u} list updated at " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            self.inCheck = False
        return True

    def __pro_load_list(self, user, arr, nowID="root", strURI="", rootIndex=0):
        isStart = True
        data = self.api[user].get_list(nowID)
        # 进入根目录
        for file in data:
            if len(self.rootPath) != 0 and rootIndex <= len(self.rootPath) - 1:
                isStart = False
                if file["type"] == "folder" and file["name"] == self.rootPath[rootIndex]:
                    self.__pro_load_list(
                        user, arr, file["file_id"], strURI + "/" + file["name"], rootIndex + 1
                    )
                continue
        if not isStart:
            return
        status = []
        for file in data:
            # 过滤排除的文件夹/文件
            if self.STATIC.util.isNeedLoad(file["type"] == "folder", str(file["name"]), self.conf):
                continue
            # 项
            item = {
                "isFolder": file["type"] == "folder",
                "createTime": 0,
                "lastOpTime": self.STATIC.util.format_time(file["updated_at"]),
                "parentId": file["parent_file_id"],
                "fileId": file["file_id"],
                "filePath": strURI + "/" + file["name"],
                "fileName": str(file["name"]),
                "fileSize": self.STATIC.util.format_size(file["size"]) if file["type"] != "folder" else -1,
                "fileType": None,
                "child": [],
                "user": user,
                "isSecret": False,
                "driveName": "aliyundrive"
            }
            if not item["isFolder"]:
                item["fileType"] = str(item["fileName"]).split(".")[-1]
            else:
                status.append(self.COMMON.thread.plz().submit(self.__pro_load_list, *(
                    user, item["child"], item["fileId"], strURI + "/" + file["name"], rootIndex)))
            arr.append(item)
        # 阻塞多线程获取文件夹内容
        for x in as_completed(status):
            pass

    def info(self, user, fid, dl=False):
        try:
            return self.api[user].get_download_url(fid)
        except Exception as e:
            self.STATIC.localMsger.error(e)
            self.STATIC.localMsger.green(f"[AliyunDrive] {user} try to login")
            try:
                self.api[user].do_refresh_token()
                return self.api[user].get_download_url(fid)
            except Exception as ee:
                self.STATIC.localMsger.error(ee)
        return False
