import requests
from lxml import etree
import re
import json


def log(*msg):
    """
    是否打印调试消息
    """
    is_log = True
    if is_log:
        print(msg)


class BJtu_Msi(object):
    def __init__(self, usercode: str, password: str):
        self.usercode = usercode
        self.password = password
        self.username = None
        self.majorname = None  # 专业名称
        self.mail_address = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
        }
        self.session = requests.Session()

    def login(self):
        """
        模拟登录北京交通大学MIS
        一定要先执行这个函数，才能正常进行其他步骤
        :return: None
        """
        login_url = 'https://mis.bjtu.edu.cn/'
        # 获取cookie
        login_page = self.session.get(url=login_url, headers=self.headers)
        # 获取被重定向了的url链接
        login_url = login_page.url
        # login_page = self.session.get(url=login_url, headers=self.headers)
        with open('login_page.html', 'w', encoding='utf-8') as f:
            f.write(login_page.text)

        login_page_tree = etree.HTML(login_page.text)
        next_value = login_page_tree.xpath('//*[@id="login"]/input[1]/@value')[0]
        csrfmiddlewaretoken_value = login_page_tree.xpath('//*[@id="login"]/input[2]/@value')[0]
        log(next_value, csrfmiddlewaretoken_value)

        # 模拟登陆
        data = {
            'next': next_value,
            'csrfmiddlewaretoken': csrfmiddlewaretoken_value,
            'loginname': self.usercode,
            'password': self.password
        }
        # 更新session的头信息 必要的步骤
        self.session.headers.update({
            'Referer': 'https://cas.bjtu.edu.cn/auth/login/',
            'Upgrade-Insecure-Requests': '1'
        })
        response = self.session.post(url=login_url, data=data)

        # 更新self信息
        response_tree = etree.HTML(response.text)
        self.name = response_tree.xpath('/html/body/div[2]/div/div[1]/div/div[1]/div/h3/a/text()')[0].split('，')[0]

    def get_acc_info(self) -> dict:
        """
        返回首页的信息 字典形式：
            1.新邮件数量: newmail_count
            2.一卡通余额: ecard_yuer
            3.网费余额: net_fee
            4.名下ip地址数量: ip_count
            5.即将过期ip数量: jjgq_ip
        :return:
        """
        acc_info_url = 'https://mis.bjtu.edu.cn/osys_ajax_wrap/'
        response = self.session.get(acc_info_url)
        acc_info = response.json()
        return acc_info

    def login_gsdb(self):
        """
        通过mis登陆研究生教育管理信息系统
        :return:
        """
        url = 'https://mis.bjtu.edu.cn/module/module/23/'
        response = self.session.get(url)
        # 从上面的响应信息中获取登陆研究生管理信息系统的链接
        response_tree = etree.HTML(response.text)
        url = response_tree.xpath('//form/@action')[0]

        # 直接对该url发起get请求，即可正常登陆
        # 自动跳转到了   https://gsdb.bjtu.edu.cn/notice/frontend/
        response = self.session.get(url=url)
        # print(response.text)

    def login_email(self):
        """
        通过mis登陆研究生教育管理信息系统
        :return:
        """
        url = 'https://mis.bjtu.edu.cn/module/module/26/'
        response = self.session.get(url)

        # 从上面的响应信息中获取登陆邮箱系统的链接 以及 验证信息
        response_tree = etree.HTML(response.text)
        url = response_tree.xpath('//form/@action')[0]
        email = response_tree.xpath('//input[@name="email"]/@value')[0]
        auth_timestamp = response_tree.xpath('//input[@name="auth_timestamp"]/@value')[0]
        auth_signature = response_tree.xpath('//input[@name="auth_signature"]/@value')[0]
        auth_type = response_tree.xpath('//input[@name="auth_type"]/@value')[0]
        auth_key = response_tree.xpath('//input[@name="auth_key"]/@value')[0]
        log('in login_email fun: ', email, auth_key, auth_type, auth_signature, auth_timestamp)
        params = {
            'email': email,
            'auth_timestamp': auth_timestamp,
            'auth_signature': auth_signature,
            'auth_type': auth_type,
            'auth_key': auth_key
        }

        # 直接对该url发起get请求，即可正常登陆
        # 自动跳转到了   https://gsdb.bjtu.edu.cn/notice/frontend/
        response = self.session.get(url=url, params=params)
        with open('mail.html', 'w', encoding='utf-8') as f:
            f.write(response.text)

        # 获取后续表单中需要的sid号
        sid = re.findall(r'sid=(.*)', response.url)[0]

        # 构造post请求中需要查询的json数据
        json_data = {"attrIds": ["email", "primary_email", "true_name", "gender", "@ou", "safelist", "refuselist"],
                     "optionalAttrIds": ["firstpage", "save_sent", "edit_mode", "aftersend_saveaddr", "maxlist", "addo",
                                         "replyf",
                                         "afterdel", "displaysender", "smtp_save_sent", "op_readreceipt",
                                         "newwindowtoreadletter", "clock_system", "display_list", "display_size",
                                         "list_brief_text", "reference_content", "preview_layout", "list_style",
                                         "shortcut", "send_card", "search_ordering_rule", "index_time_category",
                                         "multi_tab", "reply_all_mode", "query_read_status", "time_zone",
                                         "def_sec_folder", "ws_msg_notify", "ws_msg_notify_folder",
                                         "default_sender_address",
                                         "signature_position", "sms_login_notify", "app_login_notify",
                                         "subject_refw_prefix_expand", "migration_progress", "event_notify_options",
                                         "translate", "translate_condition"]}
        json_data = json.dumps(json_data)


        # 首先使用get构造post请求用的url
        url = 'https://mail.bjtu.edu.cn/coremail/s/json'
        params = {
            'sid': sid,
            'func': 'user:getAttrs'
        }
        response = self.session.get(url=url, params=params)
        url = response.url
        # 使用post请求，加上上述的json数据进行请求
        response = self.session.post(url=url, data=json_data)
        print(response.json())



if __name__ == '__main__':
    # 个人信息初始化
    spider = BJtu_Msi('学号', '密码')

    # 登录
    spider.login()

    # 获取账户信息（ajax）
    acc_info = spider.get_acc_info()
    print(acc_info)

    # 登录研究生管理系统
    spider.login_gsdb()

    # 登录邮件
    spider.login_email()
