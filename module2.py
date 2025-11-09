#!/usr/bin/env python3
"""
KIỂM THỬ DYNAMIC DATA MASKING - Phuong_AnNhonNam
Phiên bản sửa lỗi hoàn chỉnh
"""

import pyodbc
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any


class KiemThuMaskingSQLServer:
    def __init__(self):
        self.cau_hinh = {
            "server": "localhost,1434",
            "database": "Phuong_AnNhonNam",
            "driver": "{ODBC Driver 17 for SQL Server}",
        }
        # Chỉ dùng SA để kết nối, sau đó dùng EXECUTE AS để test users
        self.sa_login = {
            "username": "sa",
            "password": "Password_123#"  # Mật khẩu SA của bạn
        }
        self.contained_users = ["user_admin", "user_ketoan", "user_vanthu", "user_nhanvien"]
        self.ket_qua_kiem_thu = []

    def ket_noi_sa(self):
        """Kết nối đến SQL Server với SA"""
        try:
            chuoi_ket_noi = (
                f"Driver={self.cau_hinh['driver']};"
                f"Server={self.cau_hinh['server']};"
                f"Database={self.cau_hinh['database']};"
                f"UID={self.sa_login['username']};"
                f"PWD={self.sa_login['password']};"
                "Trusted_Connection=No;"
            )
            ket_noi = pyodbc.connect(chuoi_ket_noi)
            print("✅ Kết nối thành công với SA")
            return ket_noi
        except Exception as e:
            print(f"❌ Kết nối thất bại với SA: {str(e)}")
            return None

    def chuyen_doi_du_lieu(self, data):
        """Chuyển đổi dữ liệu để JSON serializable"""
        if isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {k: self.chuyen_doi_du_lieu(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.chuyen_doi_du_lieu(item) for item in data]
        else:
            return data

    def thuc_thi_truy_van_voi_user(self, ket_noi, user: str, truy_van: str):
        """Thực thi truy vấn với quyền của user cụ thể"""
        try:
            cursor = ket_noi.cursor()

            # Chuyển sang context của user
            cursor.execute(f"EXECUTE AS USER = '{user}';")

            # Thực thi truy vấn chính
            cursor.execute(truy_van)

            # Lấy kết quả
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()

            # Quay lại context SA
            cursor.execute("REVERT;")

            # Chuyển thành dictionary và chuyển đổi dữ liệu
            ket_qua = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                ket_qua.append(self.chuyen_doi_du_lieu(row_dict))

            return ket_qua
        except Exception as e:
            # Đảm bảo revert nếu có lỗi
            try:
                cursor.execute("REVERT;")
            except:
                pass
            print(f"❌ Lỗi truy vấn với user {user}: {str(e)}")
            return None

    def chay_test_case(self, ma_test: str, mo_ta: str, user: str, truy_van: str, dieu_kien_mong_doi: callable):
        """Chạy một test case với user cụ thể"""
        print(f"🧪 {ma_test}: {mo_ta}")

        ket_noi = self.ket_noi_sa()
        if not ket_noi:
            self.ket_qua_kiem_thu.append({
                'ma_test': ma_test, 'mo_ta': mo_ta, 'trang_thai': 'THAT_BAI', 'loi': 'Kết nối SA thất bại'
            })
            return

        try:
            ket_qua = self.thuc_thi_truy_van_voi_user(ket_noi, user, truy_van)
            ket_noi.close()

            if ket_qua and dieu_kien_mong_doi(ket_qua, user):
                trang_thai = 'THANH_CONG'
                loi = None
                print(f"   ✅ THÀNH CÔNG - {user}")
            else:
                trang_thai = 'THAT_BAI'
                loi = 'Không đạt điều kiện'
                print(f"   ❌ THẤT BẠI - {user}")

            # Chuyển đổi dữ liệu trước khi lưu
            mau_du_lieu = self.chuyen_doi_du_lieu(ket_qua[0]) if ket_qua else None

            self.ket_qua_kiem_thu.append({
                'ma_test': ma_test, 'mo_ta': mo_ta, 'user': user, 'trang_thai': trang_thai,
                'loi': loi, 'mau_du_lieu': mau_du_lieu
            })

        except Exception as e:
            print(f"   ⚠️ LỖI: {str(e)}")
            self.ket_qua_kiem_thu.append({
                'ma_test': ma_test, 'mo_ta': mo_ta, 'user': user, 'trang_thai': 'LOI', 'loi': str(e)
            })

    def kiem_thu_masking_cho_user(self, user: str, ten_user: str):
        """Kiểm thử masking cho một user cụ thể"""
        print(f"\n🔍 KIỂM THỬ CHO {ten_user} ({user})")
        print("-" * 50)

        # Test CMND
        self.chay_test_case(
            f"TC-CMND-{user}",
            f"Masking CMND",
            user,
            "SELECT TOP 1 CMND_CCCD, HO_TEN FROM CAN_BO",
            self._kiem_tra_masking_cmnd
        )

        # Test Lương
        self.chay_test_case(
            f"TC-LUONG-{user}",
            f"Masking lương",
            user,
            "SELECT TOP 1 LUONG_CO_BAN, PHU_CAP, TONG_LUONG FROM CAN_BO",
            self._kiem_tra_masking_luong
        )

        # Test Email & Điện thoại
        self.chay_test_case(
            f"TC-LIENLAC-{user}",
            f"Masking email & điện thoại",
            user,
            "SELECT TOP 1 EMAIL, DIEN_THOAI FROM CAN_BO",
            self._kiem_tra_masking_lien_lac
        )

        # Test BHXH
        self.chay_test_case(
            f"TC-BHXH-{user}",
            f"Masking BHXH",
            user,
            "SELECT TOP 1 SO_BHXH, HO_TEN FROM CAN_BO",
            self._kiem_tra_masking_bhxh
        )

    def _kiem_tra_masking_cmnd(self, ket_qua, user):
        """Kiểm tra masking CMND"""
        if not ket_qua or not ket_qua[0].get('CMND_CCCD'):
            return False

        cmnd = str(ket_qua[0]['CMND_CCCD'])
        if user == 'user_admin':
            return '****' not in cmnd  # Admin thấy đầy đủ
        else:
            return '****' in cmnd  # User khác thấy masked

    def _kiem_tra_masking_luong(self, ket_qua, user):
        """Kiểm tra masking lương"""
        if not ket_qua:
            return False

        luong = ket_qua[0].get('LUONG_CO_BAN', 0)
        if user == 'user_admin':
            return luong > 0  # Admin thấy lương thật
        else:
            return luong == 0  # User khác thấy 0

    def _kiem_tra_masking_lien_lac(self, ket_qua, user):
        """Kiểm tra masking email & điện thoại"""
        if not ket_qua:
            return False

        email = str(ket_qua[0].get('EMAIL', ''))
        dienthoai = str(ket_qua[0].get('DIEN_THOAI', ''))

        if user == 'user_admin':
            return '@' in email and '****' not in dienthoai
        else:
            return 'XXX' in email or '****' in dienthoai

    def _kiem_tra_masking_bhxh(self, ket_qua, user):
        """Kiểm tra masking BHXH"""
        if not ket_qua or not ket_qua[0].get('SO_BHXH'):
            return False

        bhxh = str(ket_qua[0]['SO_BHXH'])
        if user == 'user_admin':
            return '****' not in bhxh
        else:
            return '****' in bhxh

    def kiem_thu_phan_quyen(self):
        """Kiểm thử phân quyền bằng EXECUTE AS"""
        print(f"\n🔐 KIỂM THỬ PHÂN QUYỀN")
        print("-" * 50)

        ket_noi = self.ket_noi_sa()
        if not ket_noi:
            self.ket_qua_kiem_thu.append({
                'ma_test': 'TC-PHANQUYEN-01',
                'mo_ta': 'Kiểm tra phân quyền',
                'user': 'user_nhanvien',
                'trang_thai': 'THAT_BAI',
                'loi': 'Kết nối SA thất bại'
            })
            return

        try:
            cursor = ket_noi.cursor()

            # Chuyển sang user_nhanvien
            cursor.execute("EXECUTE AS USER = 'user_nhanvien';")

            # Thử INSERT
            try:
                cursor.execute("INSERT INTO CAN_BO (MA_CB, HO_TEN) VALUES ('TEST001', 'Test User')")
                co_quyen_insert = True
            except:
                co_quyen_insert = False

            # Thử UPDATE
            try:
                cursor.execute("UPDATE CAN_BO SET HO_TEN = 'Test' WHERE ID = 1")
                co_quyen_update = True
            except:
                co_quyen_update = False

            # Quay lại SA
            cursor.execute("REVERT;")
            ket_noi.close()

            if not co_quyen_insert and not co_quyen_update:
                trang_thai = 'THANH_CONG'
                loi = None
                print("   ✅ User không có quyền ghi - ĐÚNG")
            else:
                trang_thai = 'THAT_BAI'
                loi = 'User có quyền không mong muốn'
                print("   ❌ User có quyền ghi - SAI")

        except Exception as e:
            trang_thai = 'LOI'
            loi = str(e)
            print(f"   ⚠️ Lỗi: {loi}")

        self.ket_qua_kiem_thu.append({
            'ma_test': 'TC-PHANQUYEN-01',
            'mo_ta': 'Kiểm tra user_nhanvien không có quyền ghi',
            'user': 'user_nhanvien',
            'trang_thai': trang_thai,
            'loi': loi
        })

    def kiem_thu_toan_ven_du_lieu(self):
        """Kiểm thử tính toàn vẹn dữ liệu"""
        print(f"\n📊 KIỂM THỬ TOÀN VẸN DỮ LIỆU")
        print("-" * 50)

        # Kiểm tra số lượng bản ghi thực tế
        ket_noi = self.ket_noi_sa()
        if ket_noi:
            cursor = ket_noi.cursor()
            cursor.execute("SELECT COUNT(*) as so_luong FROM CAN_BO")
            so_luong_thuc_te = cursor.fetchone()[0]
            ket_noi.close()

            print(f"   📈 Số lượng bản ghi thực tế: {so_luong_thuc_te}")

            for user in ['user_admin', 'user_nhanvien']:
                self.chay_test_case(
                    f"TC-TOANVEN-{user}",
                    f"Số lượng bản ghi",
                    user,
                    "SELECT COUNT(*) as so_luong FROM CAN_BO",
                    lambda r, u: r[0]['so_luong'] == so_luong_thuc_te if r else False
                )

    def kiem_tra_view_cong_khai(self):
        """Kiểm tra view công khai"""
        print(f"\n👁️ KIỂM TRA VIEW CÔNG KHAI")
        print("-" * 50)

        for user in ['user_admin', 'user_ketoan', 'user_nhanvien']:
            self.chay_test_case(
                f"TC-VIEW-{user}",
                f"Truy cập view công khai",
                user,
                "SELECT TOP 1 * FROM VW_CAN_BO_CONG_KHAI",
                lambda r, u: r is not None and len(r) > 0
            )

    def hien_thi_ket_qua_chi_tiet(self):
        """Hiển thị kết quả chi tiết từng user"""
        print(f"\n🔍 KẾT QUẢ CHI TIẾT THEO USER")
        print("=" * 60)

        ket_noi = self.ket_noi_sa()
        if not ket_noi:
            return

        try:
            for user in self.contained_users:
                print(f"\n--- {user} ---")

                # Thực thi với quyền user
                cursor = ket_noi.cursor()
                cursor.execute(f"EXECUTE AS USER = '{user}';")

                # Lấy dữ liệu từ bảng (có masking)
                cursor.execute("SELECT TOP 1 MA_CB, HO_TEN, CMND_CCCD, DIEN_THOAI, EMAIL, LUONG_CO_BAN FROM CAN_BO")
                table_data = cursor.fetchone()

                # Lấy dữ liệu từ view (không có thông tin nhạy cảm)
                cursor.execute("SELECT TOP 1 * FROM VW_CAN_BO_CONG_KHAI")
                view_data = cursor.fetchone()

                cursor.execute("REVERT;")

                if table_data:
                    ma_cb, ho_ten, cmnd, dienthoai, email, luong = table_data
                    print(f"📊 BẢNG CAN_BO (Masking):")
                    print(f"   Mã CB: {ma_cb}, Họ tên: {ho_ten}")
                    print(f"   CMND: {cmnd}, Điện thoại: {dienthoai}")
                    print(f"   Email: {email}, Lương: {luong}")

                if view_data:
                    print(f"👁️ VIEW CÔNG KHAI:")
                    print(f"   {view_data}")

        except Exception as e:
            print(f"❌ Lỗi hiển thị chi tiết: {str(e)}")
        finally:
            ket_noi.close()

    def chay_tat_ca_test(self):
        """Chạy tất cả test cases"""
        print("🚀 BẮT ĐẦU KIỂM THỬ DYNAMIC DATA MASKING")
        print("=" * 60)
        print(f"Database: {self.cau_hinh['database']}")
        print(f"Server: {self.cau_hinh['server']}")
        print("Phương pháp: SA + EXECUTE AS USER")
        print("=" * 60)

        # Kiểm thử cho từng user
        self.kiem_thu_masking_cho_user('user_admin', 'Quản trị viên')
        self.kiem_thu_masking_cho_user('user_ketoan', 'Kế toán')
        self.kiem_thu_masking_cho_user('user_vanthu', 'Văn thư')
        self.kiem_thu_masking_cho_user('user_nhanvien', 'Nhân viên')

        self.kiem_thu_phan_quyen()
        self.kiem_thu_toan_ven_du_lieu()
        self.kiem_tra_view_cong_khai()

        # Hiển thị kết quả chi tiết
        self.hien_thi_ket_qua_chi_tiet()

        print("\n✅ HOÀN TẤT KIỂM THỬ")

    def tinh_toan_thong_ke(self):
        """Tính toán thống kê kết quả kiểm thử"""
        tong_test = len(self.ket_qua_kiem_thu)
        thanh_cong = len([r for r in self.ket_qua_kiem_thu if r['trang_thai'] == 'THANH_CONG'])
        that_bai = len([r for r in self.ket_qua_kiem_thu if r['trang_thai'] == 'THAT_BAI'])
        loi = len([r for r in self.ket_qua_kiem_thu if r['trang_thai'] == 'LOI'])
        ty_le_thanh_cong = (thanh_cong / tong_test * 100) if tong_test > 0 else 0

        return {
            'tong_test': tong_test,
            'thanh_cong': thanh_cong,
            'that_bai': that_bai,
            'loi': loi,
            'ty_le_thanh_cong': ty_le_thanh_cong
        }

    def _lay_ten_user_hien_thi(self, user):
        """Ánh xạ tên user sang tên hiển thị"""
        mapping = {
            'user_admin': 'Quản trị viên',
            'user_ketoan': 'Kế toán',
            'user_vanthu': 'Văn thư',
            'user_nhanvien': 'Nhân viên'
        }
        return mapping.get(user, user)

    def tao_bao_cao_txt(self):
        """Tạo báo cáo kết quả kiểm thử định dạng txt theo chuẩn TCVN"""
        thong_ke = self.tinh_toan_thong_ke()

        # Phân tích chi tiết theo user
        user_analysis = {}
        for test in self.ket_qua_kiem_thu:
            user = test.get('user', 'unknown')
            if user not in user_analysis:
                user_analysis[user] = {'total': 0, 'success': 0, 'failed': 0, 'error': 0}

            user_analysis[user]['total'] += 1
            if test['trang_thai'] == 'THANH_CONG':
                user_analysis[user]['success'] += 1
            elif test['trang_thai'] == 'THAT_BAI':
                user_analysis[user]['failed'] += 1
            else:
                user_analysis[user]['error'] += 1

        # Lấy thông tin test cases thất bại
        test_that_bai = [test for test in self.ket_qua_kiem_thu if test['trang_thai'] in ['THAT_BAI', 'LOI']]

        # Tạo nội dung báo cáo
        bao_cao = f"""
================================================================================
BÁO CÁO KIỂM THỬ DYNAMIC DATA MASKING THEO TCVN 14423:2025
================================================================================
Thời gian xuất báo cáo: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
Cơ sở dữ liệu: {self.cau_hinh['database']}
Server: {self.cau_hinh['server']}

1. THỐNG KÊ TỔNG QUAN KIỂM THỬ
--------------------------------------------------
Tổng số test cases: {thong_ke['tong_test']}
Số test cases thành công: {thong_ke['thanh_cong']}
Số test cases thất bại: {thong_ke['that_bai']}
Số test cases lỗi: {thong_ke['loi']}
Tỷ lệ thành công: {thong_ke['ty_le_thanh_cong']:.1f}%

2. PHÂN TÍCH KẾT QUẢ THEO NGƯỜI DÙNG
--------------------------------------------------"""

        # Thêm thông tin phân tích user
        for user, stats in user_analysis.items():
            ty_le_user = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            ten_user_hien_thi = self._lay_ten_user_hien_thi(user)
            bao_cao += f"\n- {ten_user_hien_thi} ({user}): {stats['success']}/{stats['total']} thành công ({ty_le_user:.1f}%)"

        bao_cao += f"""
\n3. CHI TIẾT CÁC TEST CASE THẤT BẠI
--------------------------------------------------"""

        if test_that_bai:
            for test in test_that_bai[:10]:  # Giới hạn hiển thị 10 test thất bại
                ten_user_hien_thi = self._lay_ten_user_hien_thi(test.get('user', 'unknown'))
                bao_cao += f"\n⏰ {test['ma_test']} | 👤 {ten_user_hien_thi}"
                bao_cao += f"\n   📝 {test['mo_ta']}"
                bao_cao += f"\n   ❌ {test['trang_thai']}: {test.get('loi', 'Không xác định')}"
                bao_cao += "\n"
        else:
            bao_cao += "\n✅ Không có test case nào thất bại"

        bao_cao += f"""
\n4. ĐÁNH GIÁ MỨC ĐỘ BẢO MẬT
--------------------------------------------------"""

        # Đánh giá theo tiêu chí
        danh_gia = []

        if thong_ke['ty_le_thanh_cong'] >= 90:
            danh_gia.append("✅ Tỷ lệ test thành công: ĐẠT")
        elif thong_ke['ty_le_thanh_cong'] >= 70:
            danh_gia.append("⚠️  Tỷ lệ test thành công: CHẤP NHẬN ĐƯỢC")
        else:
            danh_gia.append("❌ Tỷ lệ test thành công: KHÔNG ĐẠT")

        # Kiểm tra masking cho admin
        admin_tests = [t for t in self.ket_qua_kiem_thu if
                       t.get('user') == 'user_admin' and t['trang_thai'] == 'THANH_CONG']
        if len(admin_tests) >= 4:  # Các test cơ bản cho admin
            danh_gia.append("✅ Quyền admin: ĐẠT - Thấy dữ liệu đầy đủ")
        else:
            danh_gia.append("❌ Quyền admin: KHÔNG ĐẠT - Có vấn đề với quyền admin")

        # Kiểm tra masking cho user thường
        user_thuong_tests = [t for t in self.ket_qua_kiem_thu
                             if t.get('user') in ['user_ketoan', 'user_nhanvien']
                             and t['trang_thai'] == 'THANH_CONG']
        if len(user_thuong_tests) >= 6:  # Các test cơ bản cho user thường
            danh_gia.append("✅ Masking user thường: ĐẠT - Dữ liệu được ẩn đúng")
        else:
            danh_gia.append("❌ Masking user thường: KHÔNG ĐẠT - Dữ liệu không được ẩn đúng")

        for dg in danh_gia:
            bao_cao += f"\n{dg}"

        bao_cao += f"""
\n5. KẾT LUẬN VÀ KHUYẾN NGHỊ
--------------------------------------------------"""

        if thong_ke['ty_le_thanh_cong'] >= 90:
            bao_cao += "\n🎯 KẾT LUẬN: ✅ ĐẠT TIÊU CHUẨN"
            bao_cao += "\n\n📋 KHUYẾN NGHỊ:"
            bao_cao += "\n🔸 Duy trì hiện trạng cấu hình Dynamic Data Masking"
            bao_cao += "\n🔸 Tiếp tục giám sát định kỳ"
            bao_cao += "\n🔸 Đào tạo user về quyền truy cập dữ liệu"
        elif thong_ke['ty_le_thanh_cong'] >= 70:
            bao_cao += "\n🎯 KẾT LUẬN: ⚠️  CHẤP NHẬN ĐƯỢC"
            bao_cao += "\n\n📋 KHUYẾN NGHỊ:"
            bao_cao += "\n🔸 Kiểm tra lại cấu hình masking cho các trường thất bại"
            bao_cao += "\n🔸 Rà soát phân quyền user"
            bao_cao += "\n🔸 Thực hiện kiểm thử lại sau khi điều chỉnh"
            bao_cao += "\n🔸 Tăng cường giám sát truy cập dữ liệu nhạy cảm"
        else:
            bao_cao += "\n🎯 KẾT LUẬN: ❌ KHÔNG ĐẠT TIÊU CHUẨN"
            bao_cao += "\n\n📋 KHUYẾN NGHỊ KHẮC PHỤC:"
            bao_cao += "\n🔸 KHẨN: Kiểm tra toàn bộ cấu hình Dynamic Data Masking"
            bao_cao += "\n🔸 Rà soát lại hệ thống phân quyền user"
            bao_cao += "\n🔸 Xác minh hàm masking cho từng trường dữ liệu"
            bao_cao += "\n🔸 Kiểm tra quyền UNMASK cho các user"
            bao_cao += "\n🔸 Thực hiện kiểm thử lại sau khi khắc phục"

        bao_cao += f"""

6. THÔNG TIN KỸ THUẬT
--------------------------------------------------
Phương pháp kiểm thử: SA + EXECUTE AS USER
Số lượng user được kiểm thử: {len(user_analysis)}
Tổng số lượt truy vấn kiểm thử: {thong_ke['tong_test']}
Database: {self.cau_hinh['database']}
Phiên bản script: 3.0 (Hoàn thiện)

================================================================================
Báo cáo được tạo tự động bởi Hệ thống Kiểm thử Dynamic Data Masking
================================================================================
"""

        # Lưu file txt
        filename = f"bao_cao_masking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(bao_cao)

        print(f"\n📄 Đã tạo báo cáo: {filename}")

        # In tóm tắt ra console
        print(f"\n📊 TÓM TẮT BÁO CÁO:")
        print(f"   Tổng test: {thong_ke['tong_test']}")
        print(f"   Thành công: {thong_ke['thanh_cong']} ({thong_ke['ty_le_thanh_cong']:.1f}%)")
        print(f"   Thất bại: {thong_ke['that_bai'] + thong_ke['loi']}")

        return thong_ke['ty_le_thanh_cong']


def main():
    """Hàm chính"""
    kiem_thu = KiemThuMaskingSQLServer()

    # Hiển thị bảng phân quyền trước

    # Chạy kiểm thử
    kiem_thu.chay_tat_ca_test()
    ty_le_thanh_cong = kiem_thu.tao_bao_cao_txt()

    # Đánh giá
    if ty_le_thanh_cong >= 90:
        print("\n🎉 XUẤT SẮC - Masking hoạt động hoàn hảo!")
    elif ty_le_thanh_cong >= 70:
        print("\n⚠️  KHÁ - Cần điều chỉnh một số điểm")
    else:
        print("\n💥 CẢNH BÁO - Có vấn đề với cấu hình masking!")


if __name__ == "__main__":
    main()