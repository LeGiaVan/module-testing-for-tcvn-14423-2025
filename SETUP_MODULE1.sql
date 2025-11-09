USE Phuong_AnNhonNam;
GO

-- 1. TẠO BẢNG HỆ THỐNG NGƯỜI DÙNG
PRINT '🔧 Đang tạo bảng he_thong_nguoi_dung...';
IF EXISTS (SELECT * FROM sysobjects WHERE name='he_thong_nguoi_dung' AND xtype='U')
    DROP TABLE he_thong_nguoi_dung;

CREATE TABLE he_thong_nguoi_dung (
    username NVARCHAR(50) PRIMARY KEY,
    ho_ten NVARCHAR(100) NOT NULL,
    phong_ban NVARCHAR(50),
    chuc_vu NVARCHAR(50),
    muc_do_truy_cap INT DEFAULT 1,
    trang_thai BIT DEFAULT 1,
    ngay_tao DATETIME2 DEFAULT GETDATE()
);

-- Chèn dữ liệu mẫu
INSERT INTO he_thong_nguoi_dung (username, ho_ten, phong_ban, chuc_vu, muc_do_truy_cap) VALUES
('user_admin', N'Nguyễn Văn A', N'VĂN PHÒNG', N'Chủ tịch UBND', 4),
('user_vanthu', N'Trần Thị B', N'VĂN PHÒNG', N'Văn thư', 2),
('user_ketoan', N'Lê Văn C', N'KẾ TOÁN', N'Kế toán trưởng', 3),
('user_nhanvien', N'Phạm Thị D', N'VĂN PHÒNG', N'Chuyên viên', 1),
('user_congan', N'Hoàng Văn E', N'CÔNG AN', N'Cán bộ công an', 3);

PRINT '✅ Đã tạo xong bảng he_thong_nguoi_dung với 5 bản ghi';
GO

-- 2. TẠO BẢNG DANH MỤC TÀI SẢN
PRINT '';
PRINT '🔧 Đang tạo bảng danh_muc_tai_san...';
IF EXISTS (SELECT * FROM sysobjects WHERE name='danh_muc_tai_san' AND xtype='U')
    DROP TABLE danh_muc_tai_san;

CREATE TABLE danh_muc_tai_san (
    tai_san_id NVARCHAR(50) PRIMARY KEY,
    ten_tai_san NVARCHAR(100) NOT NULL,
    loai_tai_san NVARCHAR(50),
    muc_do_nhay_cam INT DEFAULT 1,
    phong_ban_quan_ly NVARCHAR(50),
    trang_thai BIT DEFAULT 1,
    ngay_tao DATETIME2 DEFAULT GETDATE()
);

-- Chèn dữ liệu mẫu
INSERT INTO danh_muc_tai_san (tai_san_id, ten_tai_san, loai_tai_san, muc_do_nhay_cam, phong_ban_quan_ly) VALUES
('TS001', N'Báo cáo tài chính quý I/2024', N'BÁO CÁO', 3, N'KẾ TOÁN'),
('TS002', N'Danh sách lương cán bộ', N'DANH SÁCH', 3, N'KẾ TOÁN'),
('TS003', N'Báo cáo an ninh trật tự', N'BÁO CÁO', 4, N'CÔNG AN'),
('TS004', N'Hồ sơ cán bộ', N'HỒ SƠ', 2, N'VĂN PHÒNG'),
('TS005', N'Kế hoạch công tác năm', N'KẾ HOẠCH', 1, N'VĂN PHÒNG'),
('TS006', N'Thông tin dân cư', N'DỮ LIỆU', 4, N'CÔNG AN'),
('TS007', N'Báo cáo thi đua', N'BÁO CÁO', 2, N'VĂN PHÒNG'),
('TS008', N'Quyết định nhân sự', N'QUYẾT ĐỊNH', 3, N'VĂN PHÒNG');

PRINT '✅ Đã tạo xong bảng danh_muc_tai_san với 8 bản ghi';
GO

-- 3. TẠO BẢNG LOG TRUY CẬP
PRINT '';
PRINT '🔧 Đang tạo bảng log_truy_cap...';
IF EXISTS (SELECT * FROM sysobjects WHERE name='log_truy_cap' AND xtype='U')
    DROP TABLE log_truy_cap;

CREATE TABLE log_truy_cap (
    id INT IDENTITY(1,1) PRIMARY KEY,
    thoi_gian DATETIME2 NOT NULL,
    username NVARCHAR(50) NOT NULL,
    tai_san_id NVARCHAR(50) NOT NULL,
    hanh_dong NVARCHAR(20),
    thanh_cong BIT NOT NULL,
    ly_do NVARCHAR(255),
    dia_chi_ip NVARCHAR(50),
    user_agent NVARCHAR(255)
);

-- Chèn dữ liệu log mẫu (36 bản ghi)
INSERT INTO log_truy_cap (thoi_gian, username, tai_san_id, hanh_dong, thanh_cong, ly_do) VALUES
-- Truy cập thành công
(DATEADD(HOUR, -1, GETDATE()), 'user_admin', 'TS001', 'SELECT', 1, 'Truy cập hợp lệ'),
(DATEADD(HOUR, -2, GETDATE()), 'user_ketoan', 'TS002', 'SELECT', 1, 'Truy cập hợp lệ'),
(DATEADD(HOUR, -3, GETDATE()), 'user_vanthu', 'TS004', 'SELECT', 1, 'Truy cập hợp lệ'),
(DATEADD(HOUR, -4, GETDATE()), 'user_nhanvien', 'TS005', 'SELECT', 1, 'Truy cập hợp lệ'),

-- Truy cập thất bại - Vượt quyền
(DATEADD(HOUR, -1, GETDATE()), 'user_nhanvien', 'TS001', 'SELECT', 0, N'Vượt quyền - User cấp 1 không được truy cập tài sản cấp 3'),
(DATEADD(HOUR, -1, GETDATE()), 'user_nhanvien', 'TS002', 'SELECT', 0, N'Vượt quyền - User cấp 1 không được truy cập tài sản cấp 3'),
(DATEADD(HOUR, -2, GETDATE()), 'user_vanthu', 'TS003', 'SELECT', 0, N'Vượt quyền - User cấp 2 không được truy cập tài sản cấp 4'),
(DATEADD(HOUR, -2, GETDATE()), 'user_ketoan', 'TS003', 'SELECT', 0, N'Vượt quyền - User cấp 3 không được truy cập tài sản cấp 4'),
(DATEADD(HOUR, -3, GETDATE()), 'user_nhanvien', 'TS006', 'SELECT', 0, N'Vượt quyền - User cấp 1 không được truy cập tài sản cấp 4'),

-- Thêm nhiều log thất bại khác
(DATEADD(HOUR, -5, GETDATE()), 'user_nhanvien', 'TS001', 'SELECT', 0, N'Vượt quyền - User cấp 1 không được truy cập tài sản cấp 3'),
(DATEADD(HOUR, -6, GETDATE()), 'user_vanthu', 'TS002', 'UPDATE', 0, N'Vượt quyền - User cấp 2 không được sửa tài sản cấp 3'),
(DATEADD(HOUR, -7, GETDATE()), 'user_nhanvien', 'TS008', 'SELECT', 0, N'Vượt quyền - User cấp 1 không được truy cập tài sản cấp 3'),
(DATEADD(HOUR, -8, GETDATE()), 'user_ketoan', 'TS003', 'SELECT', 0, N'Vượt quyền - User cấp 3 không được truy cập tài sản cấp 4'),
(DATEADD(HOUR, -9, GETDATE()), 'user_nhanvien', 'TS002', 'SELECT', 0, N'Vượt quyền - User cấp 1 không được truy cập tài sản cấp 3'),
(DATEADD(HOUR, -10, GETDATE()), 'user_vanthu', 'TS006', 'SELECT', 0, N'Vượt quyền - User cấp 2 không được truy cập tài sản cấp 4'),
(DATEADD(HOUR, -11, GETDATE()), 'user_ketoan', 'TS003', 'SELECT', 0, N'Vượt quyền - User cấp 3 không được truy cập tài sản cấp 4'),
(DATEADD(HOUR, -12, GETDATE()), 'user_nhanvien', 'TS001', 'SELECT', 0, N'Vượt quyền - User cấp 1 không được truy cập tài sản cấp 3'),

-- Log từ 22-26h trước (để test cảnh báo 24h)
(DATEADD(HOUR, -22, GETDATE()), 'user_congan', 'TS003', 'SELECT', 0, N'Vượt quyền - User cấp 3 không được truy cập tài sản cấp 4'),
(DATEADD(HOUR, -23, GETDATE()), 'user_vanthu', 'TS002', 'SELECT', 0, N'Vượt quyền - User cấp 2 không được truy cập tài sản cấp 3'),
(DATEADD(HOUR, -24, GETDATE()), 'user_nhanvien', 'TS001', 'SELECT', 0, N'Vượt quyền - User cấp 1 không được truy cập tài sản cấp 3'),
(DATEADD(HOUR, -25, GETDATE()), 'user_ketoan', 'TS003', 'SELECT', 0, N'Vượt quyền - User cấp 3 không được truy cập tài sản cấp 4'),
(DATEADD(HOUR, -26, GETDATE()), 'user_vanthu', 'TS006', 'SELECT', 0, N'Vượt quyền - User cấp 2 không được truy cập tài sản cấp 4');

PRINT '✅ Đã tạo xong bảng log_truy_cap với dữ liệu mẫu';
GO


-- 6. KIỂM TRA KẾT QUẢ
PRINT '';
PRINT '📊 KIỂM TRA DỮ LIỆU ĐÃ TẠO:';
PRINT '========================================';

DECLARE @count_users INT, @count_assets INT, @count_logs INT, @count_alerts INT;

SELECT @count_users = COUNT(*) FROM he_thong_nguoi_dung;
SELECT @count_assets = COUNT(*) FROM danh_muc_tai_san;
SELECT @count_logs = COUNT(*) FROM log_truy_cap;

PRINT '✅ he_thong_nguoi_dung: ' + CAST(@count_users AS NVARCHAR) + ' bản ghi';
PRINT '✅ danh_muc_tai_san: ' + CAST(@count_assets AS NVARCHAR) + ' bản ghi';
PRINT '✅ log_truy_cap: ' + CAST(@count_logs AS NVARCHAR) + ' bản ghi';
PRINT '';
PRINT '📈 THỐNG KÊ LOG TRUY CẬP:';
SELECT 
    COUNT(*) as tong_truy_cap,
    SUM(CASE WHEN thanh_cong = 1 THEN 1 ELSE 0 END) as thanh_cong,
    SUM(CASE WHEN thanh_cong = 0 THEN 1 ELSE 0 END) as that_bai,
    CAST(SUM(CASE WHEN thanh_cong = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,1)) as ty_le_thanh_cong
FROM log_truy_cap;

PRINT '';
PRINT '🎉 HOÀN TẤT KHÔI PHỤC DỮ LIỆU!';
PRINT 'Bây giờ bạn có thể chạy lại script kiểm thử bảo mật.';
GO