import pyodbc
import datetime
from typing import Dict, List
import sys


class KiemThuBaoMat_SQLServer:
    def __init__(self):
        self.ket_noi = self.tao_ket_noi_sql_server()
        if self.ket_noi:
            self.tao_bang_canh_bao()  # Tạo bảng cảnh báo nếu chưa có
            self.dong_bo_canh_bao_tu_log()  # Đồng bộ cảnh báo từ log
            self.tao_canh_bao_thoi_gian_thuc()  # Tạo cảnh báo thời gian thực mới

    def tao_ket_noi_sql_server(self):
        """Tạo kết nối đến SQL Server"""
        try:
            connection_string = (
                "Driver={ODBC Driver 17 for SQL Server};"
                "Server=localhost,1434;"
                "Database=Phuong_AnNhonNam;"
                "UID=sa;"
                "PWD=Password_123#;"
                "TrustServerCertificate=yes;"
                "Encrypt=no;"
            )
            conn = pyodbc.connect(connection_string)
            print("✅ Kết nối SQL Server thành công!")
            return conn
        except Exception as e:
            print(f"❌ Lỗi kết nối SQL Server: {e}")
            return None

    def tao_bang_canh_bao(self):
        """Tạo bảng cảnh báo vượt quyền nếu chưa tồn tại"""
        if not self.ket_noi:
            return

        cursor = self.ket_noi.cursor()
        try:
            cursor.execute('''
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='canh_bao_vuot_quyen' AND xtype='U')
                CREATE TABLE canh_bao_vuot_quyen (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    thoi_gian DATETIME2 NOT NULL,
                    username NVARCHAR(50) NOT NULL,
                    tai_san_id NVARCHAR(50) NOT NULL,
                    muc_do_user INT,
                    muc_do_tai_san INT,
                    mo_ta NVARCHAR(255),
                    trang_thai NVARCHAR(20) DEFAULT N'Chưa xử lý',
                    muc_do_uu_tien INT DEFAULT 1
                )
            ''')
            self.ket_noi.commit()
            print("✅ Đã đảm bảo tồn tại bảng canh_bao_vuot_quyen")
        except Exception as e:
            print(f"❌ Lỗi tạo bảng cảnh báo: {e}")

    def dong_bo_canh_bao_tu_log(self):
        """Đồng bộ cảnh báo từ các log truy cập thất bại"""
        if not self.ket_noi:
            return

        cursor = self.ket_noi.cursor()

        try:
            # Đếm số cảnh báo hiện có
            cursor.execute("SELECT COUNT(*) FROM canh_bao_vuot_quyen")
            so_canh_bao_hien_tai = cursor.fetchone()[0]

            if so_canh_bao_hien_tai == 0:
                print("🔄 Đang đồng bộ cảnh báo từ log truy cập thất bại...")

                # Lấy các log truy cập thất bại và tạo cảnh báo
                cursor.execute('''
                    INSERT INTO canh_bao_vuot_quyen (thoi_gian, username, tai_san_id, muc_do_user, muc_do_tai_san, mo_ta, muc_do_uu_tien)
                    SELECT 
                        l.thoi_gian,
                        l.username,
                        l.tai_san_id,
                        u.muc_do_truy_cap,
                        t.muc_do_nhay_cam,
                        'Tự động đồng bộ từ log: ' + l.ly_do,
                        CASE 
                            WHEN t.muc_do_nhay_cam = 4 THEN 1  -- Ưu tiên cao nhất
                            WHEN t.muc_do_nhay_cam = 3 THEN 2  -- Ưu tiên cao
                            ELSE 3                             -- Ưu tiên thường
                        END
                    FROM log_truy_cap l
                    INNER JOIN he_thong_nguoi_dung u ON l.username = u.username
                    INNER JOIN danh_muc_tai_san t ON l.tai_san_id = t.tai_san_id
                    WHERE l.thanh_cong = 0
                    AND NOT EXISTS (
                        SELECT 1 FROM canh_bao_vuot_quyen c 
                        WHERE c.username = l.username 
                        AND c.tai_san_id = l.tai_san_id 
                        AND c.thoi_gian = l.thoi_gian
                    )
                ''')

                so_dong_da_them = cursor.rowcount
                self.ket_noi.commit()
                print(f"✅ Đã thêm {so_dong_da_them} cảnh báo từ log truy cập thất bại")
            else:
                print(f"✅ Đã có {so_canh_bao_hien_tai} cảnh báo trong hệ thống")

        except Exception as e:
            print(f"❌ Lỗi đồng bộ cảnh báo: {e}")

    def tao_canh_bao_thoi_gian_thuc(self):
        """Tạo cảnh báo thời gian thực dựa trên phân tích mới nhất"""
        if not self.ket_noi:
            return

        cursor = self.ket_noi.cursor()

        try:
            print("🔍 Đang phân tích và tạo cảnh báo thời gian thực...")

            # Phân tích user có hành vi đáng ngờ (nhiều lần truy cập thất bại trong thời gian ngắn)
            cursor.execute('''
                INSERT INTO canh_bao_vuot_quyen (thoi_gian, username, tai_san_id, muc_do_user, muc_do_tai_san, mo_ta, muc_do_uu_tien)
                SELECT 
                    GETDATE() as thoi_gian,
                    l.username,
                    'MULTIPLE_VIOLATIONS' as tai_san_id,
                    u.muc_do_truy_cap,
                    3 as muc_do_tai_san,  -- Mức độ nghiêm trọng
                    'CẢNH BÁO: User ' + u.ho_ten + ' có ' + CAST(COUNT(*) as NVARCHAR) + 
                    ' lần truy cập thất bại trong 1 giờ qua' as mo_ta,
                    1 as muc_do_uu_tien  -- Ưu tiên cao
                FROM log_truy_cap l
                INNER JOIN he_thong_nguoi_dung u ON l.username = u.username
                WHERE l.thanh_cong = 0 
                AND l.thoi_gian > DATEADD(HOUR, -1, GETDATE())
                GROUP BY l.username, u.ho_ten, u.muc_do_truy_cap
                HAVING COUNT(*) >= 3  -- Có từ 3 lần vi phạm trở lên
                AND NOT EXISTS (
                    SELECT 1 FROM canh_bao_vuot_quyen c 
                    WHERE c.username = l.username 
                    AND c.tai_san_id = 'MULTIPLE_VIOLATIONS'
                    AND c.thoi_gian > DATEADD(HOUR, -1, GETDATE())
                )
            ''')

            so_canh_bao_moi = cursor.rowcount
            if so_canh_bao_moi > 0:
                print(f"🚨 Đã tạo {so_canh_bao_moi} cảnh báo thời gian thực")

            self.ket_noi.commit()

        except Exception as e:
            print(f"❌ Lỗi tạo cảnh báo thời gian thực: {e}")

    def cap_nhat_trang_thai_canh_bao(self, canh_bao_id: int, trang_thai: str):
        """Cập nhật trạng thái cảnh báo"""
        if not self.ket_noi:
            return False

        cursor = self.ket_noi.cursor()
        try:
            cursor.execute('''
                UPDATE canh_bao_vuot_quyen 
                SET trang_thai = ?
                WHERE id = ?
            ''', trang_thai, canh_bao_id)

            self.ket_noi.commit()
            print(f"✅ Đã cập nhật trạng thái cảnh báo #{canh_bao_id} thành: {trang_thai}")
            return True

        except Exception as e:
            print(f"❌ Lỗi cập nhật cảnh báo: {e}")
            return False

    def xoa_canh_bao_cu(self, so_ngay: int = 30):
        """Xóa cảnh báo cũ hơn số ngày chỉ định"""
        if not self.ket_noi:
            return

        cursor = self.ket_noi.cursor()
        try:
            ngay_gioi_han = datetime.datetime.now() - datetime.timedelta(days=so_ngay)

            cursor.execute('''
                DELETE FROM canh_bao_vuot_quyen 
                WHERE thoi_gian < ? AND trang_thai = N'Đã xử lý'
            ''', ngay_gioi_han)

            so_dong_da_xoa = cursor.rowcount
            self.ket_noi.commit()

            if so_dong_da_xoa > 0:
                print(f"🗑️ Đã xóa {so_dong_da_xoa} cảnh báo cũ (hơn {so_ngay} ngày)")

        except Exception as e:
            print(f"❌ Lỗi xóa cảnh báo cũ: {e}")

    def kiem_tra_cau_truc_du_lieu(self):
        """Kiểm tra cấu trúc database và dữ liệu hiện có"""
        if not self.ket_noi:
            return False

        cursor = self.ket_noi.cursor()

        print("\n🔍 KIỂM TRA CẤU TRÚC DATABASE:")
        print("-" * 50)

        # Kiểm tra các bảng tồn tại
        tables = ['log_truy_cap', 'danh_muc_tai_san', 'he_thong_nguoi_dung', 'canh_bao_vuot_quyen']

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table}'")
            if cursor.fetchone()[0] > 0:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ {table}: {count} bản ghi")
            else:
                print(f"❌ {table}: Không tồn tại")
                return False

        return True

    def phan_tich_log_truy_cap(self):
        """Phân tích log truy cập thực tế từ database"""
        if not self.ket_noi:
            return

        cursor = self.ket_noi.cursor()

        print("\n📊 PHÂN TÍCH LOG TRUY CẬP THỰC TẾ:")
        print("=" * 60)

        # Thống kê tổng quan
        cursor.execute('''
            SELECT 
                COUNT(*) as tong_truy_cap,
                SUM(CASE WHEN thanh_cong = 1 THEN 1 ELSE 0 END) as thanh_cong,
                SUM(CASE WHEN thanh_cong = 0 THEN 1 ELSE 0 END) as that_bai
            FROM log_truy_cap
        ''')
        tong_quan = cursor.fetchone()
        tong_truy_cap, thanh_cong, that_bai = tong_quan

        print(f"📈 Tổng số truy cập: {tong_truy_cap}")
        print(f"✅ Truy cập thành công: {thanh_cong}")
        print(f"❌ Truy cập thất bại: {that_bai}")
        if tong_truy_cap > 0:
            ty_le_thanh_cong = (thanh_cong / tong_truy_cap * 100)
            print(f"📊 Tỷ lệ thành công: {ty_le_thanh_cong:.1f}%")
        else:
            print("📊 Tỷ lệ thành công: 0%")

        # Top user có nhiều truy cập thất bại
        print(f"\n👤 TOP USER TRUY CẬP THẤT BẠI:")
        cursor.execute('''
            SELECT username, COUNT(*) as so_lan
            FROM log_truy_cap 
            WHERE thanh_cong = 0 
            GROUP BY username 
            ORDER BY so_lan DESC
        ''')

        results = cursor.fetchall()
        if results:
            for username, so_lan in results:
                cursor.execute('SELECT ho_ten, phong_ban FROM he_thong_nguoi_dung WHERE username = ?', username)
                user_info = cursor.fetchone()
                if user_info:
                    ho_ten, phong_ban = user_info
                    print(f"   {ho_ten} ({phong_ban}): {so_lan} lần")
                else:
                    print(f"   {username}: {so_lan} lần")
        else:
            print("   📭 Không có user nào có truy cập thất bại")

    def phan_tich_canh_bao_vuot_quyen(self):
        """Phân tích cảnh báo vượt quyền"""
        if not self.ket_noi:
            return

        cursor = self.ket_noi.cursor()

        print(f"\n🚨 PHÂN TÍCH CẢNH BÁO VƯỢT QUYỀN:")
        print("=" * 50)

        # Cảnh báo 24h gần đây
        thoi_gian_24h = datetime.datetime.now() - datetime.timedelta(hours=24)
        cursor.execute('''
            SELECT COUNT(*) 
            FROM canh_bao_vuot_quyen 
            WHERE thoi_gian > ?
        ''', thoi_gian_24h)
        canh_bao_24h = cursor.fetchone()[0]

        print(f"📈 Cảnh báo 24h gần đây: {canh_bao_24h}")

        # Phân loại cảnh báo theo mức độ ưu tiên
        cursor.execute('''
            SELECT 
                muc_do_uu_tien,
                COUNT(*) as so_luong
            FROM canh_bao_vuot_quyen 
            WHERE thoi_gian > ?
            GROUP BY muc_do_uu_tien
            ORDER BY muc_do_uu_tien ASC
        ''', thoi_gian_24h)

        print(f"📋 Phân loại theo mức độ ưu tiên:")
        results = cursor.fetchall()
        if results:
            for muc_do, so_luong in results:
                mo_ta_uu_tien = "Cao nhất" if muc_do == 1 else "Cao" if muc_do == 2 else "Thường"
                print(f"   {mo_ta_uu_tien}: {so_luong} cảnh báo")
        else:
            print("   📭 Chưa có cảnh báo nào trong 24h qua")

        # Hiển thị chi tiết cảnh báo gần đây
        print(f"\n📋 CHI TIẾT CẢNH BÁO GẦN ĐÂY (Ưu tiên cao nhất):")
        cursor.execute('''
            SELECT TOP 5 
                c.id, c.thoi_gian, c.username, c.tai_san_id, c.muc_do_user, c.muc_do_tai_san, c.mo_ta, c.trang_thai,
                u.ho_ten, t.ten_tai_san
            FROM canh_bao_vuot_quyen c
            LEFT JOIN he_thong_nguoi_dung u ON c.username = u.username
            LEFT JOIN danh_muc_tai_san t ON c.tai_san_id = t.tai_san_id
            WHERE c.muc_do_uu_tien = 1
            ORDER BY c.thoi_gian DESC
        ''')

        canh_bao_chi_tiet = cursor.fetchall()
        if canh_bao_chi_tiet:
            for canh_bao_id, thoi_gian, username, tai_san_id, user_level, asset_level, mo_ta, trang_thai, ho_ten, ten_tai_san in canh_bao_chi_tiet:
                ten_hien_thi = ho_ten if ho_ten else username
                tai_san_hien_thi = ten_tai_san if ten_tai_san else tai_san_id
                print(f"   🆔 #{canh_bao_id} | ⏰ {thoi_gian.strftime('%H:%M:%S')} | 👤 {ten_hien_thi} (Cấp {user_level})")
                print(f"   📁 {tai_san_hien_thi} (Mức {asset_level}) | 📊 {trang_thai}")
                print(f"   ⚠️  {mo_ta}")
                print(f"   {'-' * 50}")
        else:
            print("   📭 Không có cảnh báo ưu tiên cao")

    def kiem_tra_quyen_truy_cap_thuc_te(self):
        """Kiểm tra quyền truy cập dựa trên dữ liệu thực tế"""
        if not self.ket_noi:
            return

        cursor = self.ket_noi.cursor()

        print(f"\n🎯 KIỂM TRA QUYỀN TRUY CẬP THỰC TẾ:")
        print("=" * 60)

        # Lấy các truy cập thất bại gần đây để phân tích
        cursor.execute('''
            SELECT TOP 10 
                l.username, l.tai_san_id, l.ly_do,
                u.muc_do_truy_cap as user_level,
                t.muc_do_nhay_cam as asset_level
            FROM log_truy_cap l
            LEFT JOIN he_thong_nguoi_dung u ON l.username = u.username
            LEFT JOIN danh_muc_tai_san t ON l.tai_san_id = t.tai_san_id
            WHERE l.thanh_cong = 0
            ORDER BY l.thoi_gian DESC
        ''')

        violations = cursor.fetchall()

        if not violations:
            print("✅ Không có vi phạm truy cập gần đây")
            return

        print("📋 CÁC VI PHẠM TRUY CẬP GẦN ĐÂY:")
        for username, tai_san_id, ly_do, user_level, asset_level in violations:
            # Lấy thông tin user
            cursor.execute('SELECT ho_ten FROM he_thong_nguoi_dung WHERE username = ?', username)
            user_result = cursor.fetchone()
            ho_ten = user_result[0] if user_result else username

            # Lấy thông tin tài sản
            cursor.execute('SELECT ten_tai_san FROM danh_muc_tai_san WHERE tai_san_id = ?', tai_san_id)
            asset_result = cursor.fetchone()
            ten_tai_san = asset_result[0] if asset_result else tai_san_id

            print(f"   👤 {ho_ten} (Cấp {user_level})")
            print(f"   📁 {ten_tai_san} (Mức {asset_level})")
            print(f"   ❌ {ly_do}")
            print(f"   {'-' * 50}")

    def danh_gia_tieu_chuan_tcvn(self):
        """Đánh giá theo tiêu chuẩn TCVN 14423:2025"""
        if not self.ket_noi:
            return

        cursor = self.ket_noi.cursor()

        print(f"\n🏆 ĐÁNH GIÁ THEO TCVN 14423:2025:")
        print("=" * 50)

        # Lấy dữ liệu thống kê
        cursor.execute('SELECT COUNT(*) FROM log_truy_cap')
        tong_truy_cap = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM log_truy_cap WHERE thanh_cong = 0')
        that_bai = cursor.fetchone()[0]

        thoi_gian_24h = datetime.datetime.now() - datetime.timedelta(hours=24)
        cursor.execute('SELECT COUNT(*) FROM canh_bao_vuot_quyen WHERE thoi_gian > ?', thoi_gian_24h)
        canh_bao_24h = cursor.fetchone()[0]

        # Tính tỷ lệ
        ty_le_that_bai = (that_bai / tong_truy_cap * 100) if tong_truy_cap > 0 else 0

        # Đếm user nguy hiểm (có truy cập thất bại trong 24h)
        cursor.execute('''
            SELECT COUNT(DISTINCT username) 
            FROM log_truy_cap 
            WHERE thanh_cong = 0 
            AND thoi_gian > ?
        ''', thoi_gian_24h)
        user_nguy_hiem = cursor.fetchone()[0]

        # Tiêu chí đánh giá
        tieu_chi_1 = ty_le_that_bai < 10  # Dưới 10% truy cập thất bại
        tieu_chi_2 = canh_bao_24h < 15  # Dưới 15 cảnh báo/ngày
        tieu_chi_3 = user_nguy_hiem < 3  # Dưới 3 user nguy hiểm

        print(f"📊 Tỷ lệ truy cập thất bại: {ty_le_that_bai:.1f}% {'✅' if tieu_chi_1 else '❌'}")
        print(f"🚨 Cảnh báo vượt quyền/24h: {canh_bao_24h} {'✅' if tieu_chi_2 else '❌'}")
        print(f"👤 User vi phạm/24h: {user_nguy_hiem} {'✅' if tieu_chi_3 else '❌'}")

        dat_chuan = tieu_chi_1 and tieu_chi_2 and tieu_chi_3
        print(f"\n🎯 KẾT LUẬN: {'✅ ĐẠT TIÊU CHUẨN TCVN' if dat_chuan else '❌ CHƯA ĐẠT TIÊU CHUẨN'}")

        # Hiển thị chi tiết đánh giá
        print(f"\n📋 CHI TIẾT ĐÁNH GIÁ:")
        if not tieu_chi_1:
            print(f"   ❌ Tỷ lệ thất bại {ty_le_that_bai:.1f}% vượt ngưỡng 10%")
        if not tieu_chi_2:
            print(f"   ❌ Số cảnh báo {canh_bao_24h} vượt ngưỡng 15/ngày")
        if not tieu_chi_3:
            print(f"   ❌ Số user vi phạm {user_nguy_hiem} vượt ngưỡng 3 user")

    def hien_thi_log_mau(self):
        """Hiển thị log mẫu từ database"""
        if not self.ket_noi:
            return

        cursor = self.ket_noi.cursor()

        print(f"\n📋 LOG TRUY CẬP MẪU:")
        print("=" * 80)

        cursor.execute('''
            SELECT TOP 5 
                l.thoi_gian, l.username, l.tai_san_id, l.hanh_dong, l.thanh_cong, l.ly_do,
                u.ho_ten, t.ten_tai_san
            FROM log_truy_cap l
            LEFT JOIN he_thong_nguoi_dung u ON l.username = u.username
            LEFT JOIN danh_muc_tai_san t ON l.tai_san_id = t.tai_san_id
            ORDER BY l.thoi_gian DESC
        ''')

        logs = cursor.fetchall()
        if logs:
            for log in logs:
                thoi_gian, username, tai_san_id, hanh_dong, thanh_cong, ly_do, ho_ten, ten_tai_san = log
                trang_thai = "✅" if thanh_cong else "❌"
                ten_hien_thi = ho_ten if ho_ten else username
                tai_san_hien_thi = ten_tai_san if ten_tai_san else tai_san_id

                print(
                    f"{thoi_gian.strftime('%H:%M:%S')} | {ten_hien_thi:15} | {tai_san_hien_thi:25} | {hanh_dong:10} | {trang_thai} {ly_do}")
        else:
            print("📭 Không có log truy cập nào")

    def xuat_bao_cao_txt(self, ten_file=None):
        """Xuất báo cáo đầy đủ ra file txt"""
        if not self.ket_noi:
            print("❌ Không thể xuất báo cáo - Mất kết nối database")
            return

        if ten_file is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            ten_file = f"BaoCaoBaoMat_TCVN_{timestamp}.txt"

        try:
            with open(ten_file, 'w', encoding='utf-8') as f:
                # Header báo cáo
                f.write("=" * 80 + "\n")
                f.write("BÁO CÁO KIỂM THỬ BẢO MẬT THEO TCVN 14423:2025\n")
                f.write("=" * 80 + "\n")
                f.write(f"Thời gian xuất báo cáo: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Cơ sở dữ liệu: Phuong_AnNhonNam\n")
                f.write("\n")

                cursor = self.ket_noi.cursor()

                # 1. THỐNG KÊ TỔNG QUAN
                f.write("1. THỐNG KÊ TỔNG QUAN HỆ THỐNG\n")
                f.write("-" * 50 + "\n")

                cursor.execute('SELECT COUNT(*) FROM log_truy_cap')
                tong_truy_cap = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM log_truy_cap WHERE thanh_cong = 0')
                that_bai = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM canh_bao_vuot_quyen')
                tong_canh_bao = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(DISTINCT username) FROM he_thong_nguoi_dung')
                tong_user = cursor.fetchone()[0]

                f.write(f"Tổng số user trong hệ thống: {tong_user}\n")
                f.write(f"Tổng số lượt truy cập: {tong_truy_cap}\n")
                f.write(f"Số truy cập thất bại: {that_bai}\n")
                f.write(f"Tổng số cảnh báo: {tong_canh_bao}\n")
                if tong_truy_cap > 0:
                    ty_le_thanh_cong = ((tong_truy_cap - that_bai) / tong_truy_cap * 100)
                    f.write(f"Tỷ lệ thành công: {ty_le_thanh_cong:.1f}%\n")
                else:
                    f.write(f"Tỷ lệ thành công: 0%\n")
                f.write("\n")

                # 2. PHÂN TÍCH USER CÓ NGUY CƠ
                f.write("2. PHÂN TÍCH USER CÓ NGUY CƠ BẢO MẬT\n")
                f.write("-" * 50 + "\n")

                cursor.execute('''
                    SELECT username, COUNT(*) as so_lan
                    FROM log_truy_cap 
                    WHERE thanh_cong = 0 
                    GROUP BY username 
                    ORDER BY so_lan DESC
                ''')

                user_violations = cursor.fetchall()
                if user_violations:
                    for username, so_lan in user_violations:
                        cursor.execute('SELECT ho_ten, phong_ban FROM he_thong_nguoi_dung WHERE username = ?', username)
                        user_info = cursor.fetchone()
                        if user_info:
                            ho_ten, phong_ban = user_info
                            f.write(f"- {ho_ten} ({phong_ban}): {so_lan} lần truy cập thất bại\n")
                else:
                    f.write("- Không có user nào có truy cập thất bại\n")

                f.write("\n")

                # 3. CẢNH BÁO NGHIÊM TRỌNG
                f.write("3. CẢNH BÁO TRUY CẬP MỨC ĐỘ CAO\n")
                f.write("-" * 50 + "\n")

                thoi_gian_24h = datetime.datetime.now() - datetime.timedelta(hours=24)
                cursor.execute('SELECT COUNT(*) FROM canh_bao_vuot_quyen WHERE thoi_gian > ?', thoi_gian_24h)
                canh_bao_24h = cursor.fetchone()[0]

                f.write(f"Số cảnh báo mức ưu tiên cao trong 24h: {canh_bao_24h}\n\n")

                cursor.execute('''
                    SELECT TOP 5 c.thoi_gian, u.ho_ten, t.ten_tai_san, c.muc_do_tai_san, c.mo_ta, c.muc_do_uu_tien
                    FROM canh_bao_vuot_quyen c
                    LEFT JOIN he_thong_nguoi_dung u ON c.username = u.username
                    LEFT JOIN danh_muc_tai_san t ON c.tai_san_id = t.tai_san_id
                    WHERE c.muc_do_uu_tien = 1
                    ORDER BY c.thoi_gian DESC
                ''')

                high_alerts = cursor.fetchall()
                if high_alerts:
                    for thoi_gian, ho_ten, ten_tai_san, muc_do, mo_ta, uu_tien in high_alerts:
                        f.write(f"⏰ {thoi_gian.strftime('%d/%m %H:%M')} | 👤 {ho_ten}\n")
                        f.write(f"   📁 {ten_tai_san} (Mức {muc_do}, Ưu tiên: {uu_tien})\n")
                        f.write(f"   ⚠️  {mo_ta}\n\n")
                else:
                    f.write("📭 Không có cảnh báo mức độ cao\n\n")

                # 4. ĐÁNH GIÁ THEO TCVN
                f.write("4. ĐÁNH GIÁ THEO TCVN 14423:2025\n")
                f.write("-" * 50 + "\n")

                cursor.execute('''
                    SELECT COUNT(DISTINCT username) 
                    FROM log_truy_cap 
                    WHERE thanh_cong = 0 
                    AND thoi_gian > ?
                ''', thoi_gian_24h)
                user_nguy_hiem = cursor.fetchone()[0]

                ty_le_that_bai = (that_bai / tong_truy_cap * 100) if tong_truy_cap > 0 else 0

                # Tiêu chí đánh giá
                tieu_chi_1 = ty_le_that_bai < 10
                tieu_chi_2 = canh_bao_24h < 15
                tieu_chi_3 = user_nguy_hiem < 3

                f.write(
                    f"📊 Tỷ lệ truy cập thất bại: {ty_le_that_bai:.1f}% {'✅ ĐẠT' if tieu_chi_1 else '❌ KHÔNG ĐẠT'}\n")
                f.write(f"🚨 Cảnh báo vượt quyền/24h: {canh_bao_24h} {'✅ ĐẠT' if tieu_chi_2 else '❌ KHÔNG ĐẠT'}\n")
                f.write(f"👤 User vi phạm/24h: {user_nguy_hiem} {'✅ ĐẠT' if tieu_chi_3 else '❌ KHÔNG ĐẠT'}\n")

                dat_chuan = tieu_chi_1 and tieu_chi_2 and tieu_chi_3
                f.write(f"\n🎯 KẾT LUẬN: {'✅ ĐẠT TIÊU CHUẨN TCVN' if dat_chuan else '❌ CHƯA ĐẠT TIÊU CHUẨN'}\n")

                # 5. KHUYẾN NGHỊ
                f.write("\n5. KHUYẾN NGHỊ CẢI THIỆN\n")
                f.write("-" * 50 + "\n")

                if not tieu_chi_1:
                    f.write("🔸 Rà soát lại hệ thống phân quyền - tỷ lệ thất bại quá cao\n")
                if not tieu_chi_2:
                    f.write("🔸 Tăng cường giám sát các cảnh báo vượt quyền\n")
                if not tieu_chi_3:
                    f.write("🔸 Đào tạo lại user về quy định truy cập dữ liệu\n")

                if dat_chuan:
                    f.write("🔸 Duy trì hiện trạng và tiếp tục giám sát định kỳ\n")
                else:
                    f.write("🔸 Ưu tiên xử lý các cảnh báo mức ưu tiên cao trước\n")
                    f.write("🔸 Xem xét đào tạo nâng cao nhận thức bảo mật\n")

                f.write("\n" + "=" * 80 + "\n")
                f.write("Báo cáo được tạo tự động bởi Hệ thống Kiểm thử TCVN 14423:2025\n")
                f.write("=" * 80 + "\n")

            print(f"✅ Đã xuất báo cáo: {ten_file}")
            return ten_file

        except Exception as e:
            print(f"❌ Lỗi xuất báo cáo: {e}")
            return None


def main():
    """Hàm thực thi chính"""
    print("🚀 BẮT ĐẦU KIỂM THỬ BẢO MẬT THEO TCVN")
    print("=" * 60)

    kiem_thu = KiemThuBaoMat_SQLServer()

    if not kiem_thu.ket_noi:
        print("❌ Không thể kết nối database. Dừng kiểm thử.")
        return

    # Kiểm tra cấu trúc database
    if not kiem_thu.kiem_tra_cau_truc_du_lieu():
        print("❌ Cấu trúc database không đầy đủ. Dừng kiểm thử.")
        return

    # Thực hiện các kiểm thử
    kiem_thu.phan_tich_log_truy_cap()
    kiem_thu.phan_tich_canh_bao_vuot_quyen()
    kiem_thu.kiem_tra_quyen_truy_cap_thuc_te()
    kiem_thu.danh_gia_tieu_chuan_tcvn()
    kiem_thu.hien_thi_log_mau()

    # Quản lý cảnh báo
    kiem_thu.xoa_canh_bao_cu(30)  # Xóa cảnh báo cũ hơn 30 ngày

    kiem_thu.xuat_bao_cao_txt()

    print(f"\n✅ HOÀN TẤT KIỂM THỬ")


if __name__ == "__main__":
    main()