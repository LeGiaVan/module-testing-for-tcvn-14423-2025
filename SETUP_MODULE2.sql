-- SETUP DYNAMIC DATA MASKING - KHÔNG XÓA DATABASE
-- Database: Phuong_AnNhonNam

USE Phuong_AnNhonNam;
GO

PRINT '================================================================================';
PRINT 'THIẾT LẬP DYNAMIC DATA MASKING - BẢO TOÀN DỮ LIỆU HIỆN CÓ';
PRINT '================================================================================';
GO

-- KIỂM TRA VÀ TẠO BẢNG CAN_BO NẾU CHƯA TỒN TẠI
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='CAN_BO' AND xtype='U')
BEGIN
    PRINT '🔧 Đang tạo bảng CAN_BO...';
    
    CREATE TABLE CAN_BO (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        MA_CB VARCHAR(20) UNIQUE NOT NULL,
        HO_TEN NVARCHAR(100) NOT NULL,
        CHUC_VU NVARCHAR(50),
        PHONG_BAN NVARCHAR(50),
        CMND_CCCD VARCHAR(20),
        SO_BHXH VARCHAR(20),
        NGAY_SINH DATE,
        GIOI_TINH NVARCHAR(10) CHECK (GIOI_TINH IN (N'Nam', N'Nữ')),
        DIEN_THOAI VARCHAR(15),
        EMAIL VARCHAR(100),
        LUONG_CO_BAN DECIMAL(15,2) CHECK (LUONG_CO_BAN >= 0),
        PHU_CAP DECIMAL(15,2) CHECK (PHU_CAP >= 0),
        TONG_LUONG DECIMAL(15,2),
        DIA_CHI NVARCHAR(200),
        TRANG_THAI BIT DEFAULT 1,
        NGAY_TAO DATETIME DEFAULT GETDATE(),
        NGUOI_TAO NVARCHAR(100) DEFAULT SYSTEM_USER
    );
    
    -- Chèn dữ liệu mẫu
    INSERT INTO CAN_BO (MA_CB, HO_TEN, CHUC_VU, PHONG_BAN, CMND_CCCD, SO_BHXH, NGAY_SINH, GIOI_TINH, DIEN_THOAI, EMAIL, LUONG_CO_BAN, PHU_CAP, TONG_LUONG, DIA_CHI) VALUES
    ('CB001', N'Nguyễn Văn A', N'Chủ tịch UBND', N'VĂN PHÒNG', '079123456789', 'BHXH00123456', '1975-03-15', N'Nam', '0912345678', 'nguyenvana@annhonnam.gov.vn', 18500000, 6500000, 25000000, N'Khu phố 1, Phường An Nhơn Nam'),
    ('CB002', N'Trần Thị B', N'Kế toán trưởng', N'KẾ TOÁN', '079987654321', 'BHXH00654321', '1980-07-22', N'Nữ', '0918765432', 'tranthib@annhonnam.gov.vn', 12500000, 5500000, 18000000, N'Khu phố 2, Phường An Nhơn Nam'),
    ('CB003', N'Lê Văn C', N'Chuyên viên Địa chính', N'ĐỊA CHÍNH', '079456123789', 'BHXH00789123', '1985-11-30', N'Nam', '0913456789', 'levanc@annhonnam.gov.vn', 9500000, 2500000, 12000000, N'Khu phố 3, Phường An Nhơn Nam'),
    ('CB004', N'Phạm Thị D', N'Văn thư', N'VĂN PHÒNG', '079789456123', 'BHXH00456789', '1990-05-18', N'Nữ', '0914567890', 'phamthid@annhonnam.gov.vn', 7500000, 2500000, 10000000, N'Khu phố 4, Phường An Nhơn Nam'),
    ('CB005', N'Hoàng Văn E', N'Cán bộ Văn hóa', N'VĂN HÓA', '079321654987', 'BHXH00321654', '1988-12-10', N'Nam', '0915678901', 'hoangvane@annhonnam.gov.vn', 8500000, 2500000, 11000000, N'Khu phố 5, Phường An Nhơn Nam');
    
    PRINT 'V Đã tạo và chèn dữ liệu vào bảng CAN_BO';
END
ELSE
BEGIN
    PRINT 'V Bảng CAN_BO đã tồn tại';
    
    -- Kiểm tra xem có dữ liệu không
    DECLARE @SoBanGhi INT;
    SELECT @SoBanGhi = COUNT(*) FROM CAN_BO;
    PRINT '   Số bản ghi hiện có: ' + CAST(@SoBanGhi AS VARCHAR);
END
GO

-- THU HỒI QUYỀN MẶC ĐỊNH TỪ PUBLIC (QUAN TRỌNG)
PRINT '🔐 Đang thu hồi quyền PUBLIC...';
REVOKE SELECT ON CAN_BO TO PUBLIC;
GO

-- TẠO USER NẾU CHƯA TỒN TẠI
PRINT '👤 Đang tạo user (nếu chưa tồn tại)...';

IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'user_admin')
    CREATE USER user_admin WITH PASSWORD = 'Admin123!';
ELSE
    PRINT '   V user_admin đã tồn tại';

IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'user_vanthu')
    CREATE USER user_vanthu WITH PASSWORD = 'VanThu123!';
ELSE
    PRINT '   V user_vanthu đã tồn tại';

IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'user_ketoan')
    CREATE USER user_ketoan WITH PASSWORD = 'KeToan123!';
ELSE
    PRINT '   V user_ketoan đã tồn tại';

IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = 'user_nhanvien')
    CREATE USER user_nhanvien WITH PASSWORD = 'NhanVien123!';
ELSE
    PRINT '   V user_nhanvien đã tồn tại';
GO

-- XÓA USER KHỎI CÁC ROLE MẶC ĐỊNH (QUAN TRỌNG)
PRINT '🔧 Đang điều chỉnh quyền user...';

BEGIN TRY
    ALTER ROLE db_datareader DROP MEMBER user_ketoan;
END TRY
BEGIN CATCH
    PRINT '   ℹ️  user_ketoan không trong db_datareader';
END CATCH

BEGIN TRY
    ALTER ROLE db_datareader DROP MEMBER user_vanthu;
END TRY
BEGIN CATCH
    PRINT '   ℹ️  user_vanthu không trong db_datareader';
END CATCH

BEGIN TRY
    ALTER ROLE db_datareader DROP MEMBER user_nhanvien;
END TRY
BEGIN CATCH
    PRINT '   ℹ️  user_nhanvien không trong db_datareader';
END CATCH

BEGIN TRY
    ALTER ROLE db_datawriter DROP MEMBER user_ketoan;
END TRY
BEGIN CATCH
    PRINT '   ℹ️  user_ketoan không trong db_datawriter';
END CATCH

BEGIN TRY
    ALTER ROLE db_datawriter DROP MEMBER user_nhanvien;
END TRY
BEGIN CATCH
    PRINT '   ℹ️  user_nhanvien không trong db_datawriter';
END CATCH
GO

-- CẤP QUYỀN CHÍNH XÁC
PRINT '🎯 Đang cấp quyền chính xác...';

-- user_admin
IF NOT EXISTS (
    SELECT * FROM sys.database_role_members rm 
    JOIN sys.database_principals r ON rm.role_principal_id = r.principal_id
    JOIN sys.database_principals m ON rm.member_principal_id = m.principal_id
    WHERE r.name = 'db_owner' AND m.name = 'user_admin'
)
BEGIN
    ALTER ROLE db_owner ADD MEMBER user_admin;
    PRINT '   V Thêm user_admin vào db_owner';
END
ELSE
    PRINT '   V user_admin đã trong db_owner';

-- CẤP QUYỀN UNMASK CHO ADMIN
GRANT UNMASK TO user_admin;
PRINT '   V Cấp quyền UNMASK cho user_admin';

-- Cấp quyền cụ thể cho từng user
GRANT SELECT, INSERT, UPDATE ON CAN_BO TO user_vanthu;
PRINT '   V Cấp quyền SELECT, INSERT, UPDATE cho user_vanthu';

GRANT SELECT ON CAN_BO TO user_ketoan;
PRINT '   V Cấp quyền SELECT cho user_ketoan';

GRANT SELECT ON CAN_BO TO user_nhanvien;
PRINT '   V Cấp quyền SELECT cho user_nhanvien';
GO

-- ÁP DỤNG DYNAMIC DATA MASKING
PRINT '🎭 Đang áp dụng Dynamic Data Masking...';

-- Kiểm tra và áp dụng masking cho từng cột
IF NOT EXISTS (
    SELECT * FROM sys.masked_columns mc 
    JOIN sys.tables t ON mc.object_id = t.object_id 
    WHERE t.name = 'CAN_BO' AND mc.name = 'CMND_CCCD'
)
BEGIN
    ALTER TABLE CAN_BO ALTER COLUMN CMND_CCCD ADD MASKED WITH (FUNCTION = 'partial(3,"*******",3)');
    PRINT '   V Áp dụng masking cho CMND_CCCD';
END

IF NOT EXISTS (
    SELECT * FROM sys.masked_columns mc 
    JOIN sys.tables t ON mc.object_id = t.object_id 
    WHERE t.name = 'CAN_BO' AND mc.name = 'SO_BHXH'
)
BEGIN
    ALTER TABLE CAN_BO ALTER COLUMN SO_BHXH ADD MASKED WITH (FUNCTION = 'partial(4,"******",2)');
    PRINT '   V Áp dụng masking cho SO_BHXH';
END

IF NOT EXISTS (
    SELECT * FROM sys.masked_columns mc 
    JOIN sys.tables t ON mc.object_id = t.object_id 
    WHERE t.name = 'CAN_BO' AND mc.name = 'EMAIL'
)
BEGIN
    ALTER TABLE CAN_BO ALTER COLUMN EMAIL ADD MASKED WITH (FUNCTION = 'email()');
    PRINT '   V Áp dụng masking cho EMAIL';
END

IF NOT EXISTS (
    SELECT * FROM sys.masked_columns mc 
    JOIN sys.tables t ON mc.object_id = t.object_id 
    WHERE t.name = 'CAN_BO' AND mc.name = 'DIEN_THOAI'
)
BEGIN
    ALTER TABLE CAN_BO ALTER COLUMN DIEN_THOAI ADD MASKED WITH (FUNCTION = 'partial(3,"*******",2)');
    PRINT '   V Áp dụng masking cho DIEN_THOAI';
END

IF NOT EXISTS (
    SELECT * FROM sys.masked_columns mc 
    JOIN sys.tables t ON mc.object_id = t.object_id 
    WHERE t.name = 'CAN_BO' AND mc.name = 'LUONG_CO_BAN'
)
BEGIN
    ALTER TABLE CAN_BO ALTER COLUMN LUONG_CO_BAN ADD MASKED WITH (FUNCTION = 'default()');
    PRINT '   V Áp dụng masking cho LUONG_CO_BAN';
END

IF NOT EXISTS (
    SELECT * FROM sys.masked_columns mc 
    JOIN sys.tables t ON mc.object_id = t.object_id 
    WHERE t.name = 'CAN_BO' AND mc.name = 'PHU_CAP'
)
BEGIN
    ALTER TABLE CAN_BO ALTER COLUMN PHU_CAP ADD MASKED WITH (FUNCTION = 'default()');
    PRINT '   V Áp dụng masking cho PHU_CAP';
END

IF NOT EXISTS (
    SELECT * FROM sys.masked_columns mc 
    JOIN sys.tables t ON mc.object_id = t.object_id 
    WHERE t.name = 'CAN_BO' AND mc.name = 'TONG_LUONG'
)
BEGIN
    ALTER TABLE CAN_BO ALTER COLUMN TONG_LUONG ADD MASKED WITH (FUNCTION = 'default()');
    PRINT '   V Áp dụng masking cho TONG_LUONG';
END
GO

-- TẠO VIEW CÔNG KHAI NẾU CHƯA TỒN TẠI
PRINT '👁️ Đang tạo view công khai...';

IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='VW_CAN_BO_CONG_KHAI' AND xtype='V')
BEGIN
    EXEC('
        CREATE VIEW VW_CAN_BO_CONG_KHAI AS
        SELECT 
            MA_CB,
            HO_TEN,
            CHUC_VU,
            PHONG_BAN,
            NGAY_SINH,
            GIOI_TINH,
            DIA_CHI,
            TRANG_THAI,
            YEAR(GETDATE()) - YEAR(NGAY_SINH) AS TUOI
        FROM CAN_BO
        WHERE TRANG_THAI = 1
    ');
    PRINT '   V Đã tạo view VW_CAN_BO_CONG_KHAI';
END
ELSE
    PRINT '   V View VW_CAN_BO_CONG_KHAI đã tồn tại';
GO

-- CẤP QUYỀN CHO VIEW
PRINT '🔐 Đang cấp quyền cho view...';
GRANT SELECT ON VW_CAN_BO_CONG_KHAI TO user_nhanvien, user_ketoan, user_vanthu;
PRINT '   V Đã cấp quyền SELECT trên view cho user_nhanvien, user_ketoan, user_vanthu';
GO

-- KIỂM TRA KẾT QUẢ
PRINT '';
PRINT '================================================================================';
PRINT 'KIỂM TRA KẾT QUẢ THIẾT LẬP';
PRINT '================================================================================';
GO

-- TEST PHÂN QUYỀN CHI TIẾT
PRINT '=== KIỂM TRA PHÂN QUYỀN ===';

EXECUTE AS USER = 'user_ketoan';
SELECT 
    'user_ketoan' as user_name,
    HAS_PERMS_BY_NAME('dbo.CAN_BO', 'OBJECT', 'SELECT') as can_select,
    HAS_PERMS_BY_NAME('dbo.CAN_BO', 'OBJECT', 'INSERT') as can_insert,
    HAS_PERMS_BY_NAME('dbo.CAN_BO', 'OBJECT', 'UPDATE') as can_update,
    HAS_PERMS_BY_NAME('', 'DATABASE', 'UNMASK') as can_unmask;
REVERT;
GO

EXECUTE AS USER = 'user_nhanvien';
SELECT 
    'user_nhanvien' as user_name,
    HAS_PERMS_BY_NAME('dbo.CAN_BO', 'OBJECT', 'SELECT') as can_select,
    HAS_PERMS_BY_NAME('dbo.CAN_BO', 'OBJECT', 'INSERT') as can_insert,
    HAS_PERMS_BY_NAME('dbo.CAN_BO', 'OBJECT', 'UPDATE') as can_update,
    HAS_PERMS_BY_NAME('', 'DATABASE', 'UNMASK') as can_unmask;
REVERT;
GO

EXECUTE AS USER = 'user_admin';
SELECT 
    'user_admin' as user_name,
    HAS_PERMS_BY_NAME('dbo.CAN_BO', 'OBJECT', 'SELECT') as can_select,
    HAS_PERMS_BY_NAME('dbo.CAN_BO', 'OBJECT', 'INSERT') as can_insert,
    HAS_PERMS_BY_NAME('dbo.CAN_BO', 'OBJECT', 'UPDATE') as can_update,
    HAS_PERMS_BY_NAME('', 'DATABASE', 'UNMASK') as can_unmask;
REVERT;
GO

-- Test masking với user ketoan
PRINT '';
PRINT '=== TEST MASKING VỚI user_ketoan (dữ liệu sẽ bị ẩn) ===';
EXECUTE AS USER = 'user_ketoan';
SELECT TOP 2
    MA_CB,
    HO_TEN,
    CMND_CCCD AS [CMND_MASKED],
    DIEN_THOAI AS [DIEN_THOAI_MASKED],
    EMAIL AS [EMAIL_MASKED],
    LUONG_CO_BAN AS [LUONG_MASKED]
FROM CAN_BO;
REVERT;
GO

-- So sánh với admin (dữ liệu đầy đủ)
PRINT '';
PRINT '=== SO SÁNH VỚI user_admin (dữ liệu đầy đủ) ===';
EXECUTE AS USER = 'user_admin';
SELECT TOP 2
    MA_CB,
    HO_TEN,
    CMND_CCCD,
    DIEN_THOAI,
    EMAIL,
    LUONG_CO_BAN
FROM CAN_BO;
REVERT;
GO

-- Xác thực thiết lập
PRINT '';
PRINT '=== XÁC THỰC DYNAMIC DATA MASKING ===';
SELECT 
    c.name AS column_name, 
    c.is_masked,
    c.masking_function
FROM sys.masked_columns c
JOIN sys.tables t ON c.object_id = t.object_id
WHERE t.name = 'CAN_BO';
GO

PRINT '';
PRINT '=== DANH SÁCH USER VÀ QUYỀN ===';
SELECT 
    dp.name AS user_name,
    dp.type_desc AS user_type,
    CASE WHEN HAS_PERMS_BY_NAME('dbo.CAN_BO', 'OBJECT', 'SELECT') = 1 THEN 'V' ELSE 'X' END AS select_perm,
    CASE WHEN HAS_PERMS_BY_NAME('dbo.CAN_BO', 'OBJECT', 'INSERT') = 1 THEN 'V' ELSE 'X' END AS insert_perm,
    CASE WHEN HAS_PERMS_BY_NAME('dbo.CAN_BO', 'OBJECT', 'UPDATE') = 1 THEN 'V' ELSE 'X' END AS update_perm,
    CASE WHEN HAS_PERMS_BY_NAME('', 'DATABASE', 'UNMASK') = 1 THEN 'V' ELSE 'X' END AS unmask_perm
FROM sys.database_principals dp
WHERE dp.name LIKE 'user_%';
GO

-- KIỂM TRA CÁC BẢNG KHÁC VẪN TỒN TẠI
PRINT '';
PRINT '=== KIỂM TRA CÁC BẢNG KHÁC (ĐÃ SỬA) ===';
SELECT 
    table_name AS [Table Name],
    CASE 
        WHEN EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = required_tables.table_name) 
        THEN 'V TỒN TẠI' 
        ELSE 'X KHÔNG TỒN TẠI' 
    END AS [Status]
FROM (VALUES 
    ('log_truy_cap'),
    ('danh_muc_tai_san'), 
    ('he_thong_nguoi_dung'),
    ('canh_bao_vuot_quyen'),
    ('CAN_BO')
) AS required_tables(table_name);
GO

PRINT '';
PRINT '================================================================================';
PRINT 'V THIẾT LẬP HOÀN TẤT THÀNH CÔNG!';
PRINT '🔑 Có thể kết nối với các user sau:';
PRINT '   - user_ketoan / KeToan123!';
PRINT '   - user_nhanvien / NhanVien123!'; 
PRINT '   - user_admin / Admin123!';
PRINT '📊 Database: Phuong_AnNhonNam';
PRINT '👤 Users: user_admin, user_vanthu, user_ketoan, user_nhanvien';
PRINT '💾 DỮ LIỆU CÁC BẢNG KHÁC ĐƯỢC BẢO TOÀN';
PRINT '================================================================================';



-- TEST LẠI SAU KHI CHẠY SETUP
USE Phuong_AnNhonNam;
GO

PRINT '=== TEST USER_KETOAN SAU KHI SETUP ===';
EXECUTE AS USER = 'user_ketoan';
SELECT 
    USER_NAME() as current_user,
    HAS_PERMS_BY_NAME('dbo.CAN_BO', 'OBJECT', 'SELECT') as can_select
FROM CAN_BO;
REVERT;
GO

PRINT '=== KIỂM TRA MASKING VỚI USER_KETOAN ===';
EXECUTE AS USER = 'user_admin';
SELECT TOP 2 
    MA_CB,
    HO_TEN,
    CMND_CCCD as CMND_MASKED,
    DIEN_THOAI as DIEN_THOAI_MASKED,
    EMAIL as EMAIL_MASKED,
    LUONG_CO_BAN as LUONG_MASKED
FROM CAN_BO;
REVERT;