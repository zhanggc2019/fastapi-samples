#!/usr/bin/env python3
"""
测试bcrypt版本兼容性
"""
import sys

def test_bcrypt_import():
    """测试bcrypt导入"""
    print("1. 测试bcrypt导入...")
    try:
        import bcrypt
        print(f"   ✅ bcrypt导入成功，版本: {bcrypt.__version__}")
        return True
    except Exception as e:
        print(f"   ❌ bcrypt导入失败: {e}")
        return False

def test_passlib_import():
    """测试passlib导入"""
    print("\n2. 测试passlib导入...")
    try:
        import passlib
        print(f"   ✅ passlib导入成功，版本: {passlib.__version__}")
        return True
    except Exception as e:
        print(f"   ❌ passlib导入失败: {e}")
        return False

def test_passlib_bcrypt_context():
    """测试passlib的bcrypt上下文"""
    print("\n3. 测试passlib的bcrypt上下文...")
    try:
        from passlib.context import CryptContext
        
        # 创建bcrypt上下文（和项目中一样的配置）
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # 测试密码哈希
        test_password = "test_password_123"
        hashed = pwd_context.hash(test_password)
        print(f"   ✅ 密码哈希成功: {hashed[:30]}...")
        
        # 测试密码验证
        is_valid = pwd_context.verify(test_password, hashed)
        print(f"   ✅ 密码验证成功: {is_valid}")
        
        # 测试错误密码
        is_invalid = pwd_context.verify("wrong_password", hashed)
        print(f"   ✅ 错误密码验证: {is_invalid}")
        
        return True
    except Exception as e:
        print(f"   ❌ passlib bcrypt上下文测试失败: {e}")
        return False

def test_security_module():
    """测试项目的security模块"""
    print("\n4. 测试项目的security模块...")
    try:
        # 添加项目路径
        sys.path.insert(0, '.')
        
        from core.security import get_password_hash, verify_password
        
        # 测试密码哈希
        test_password = "security_test_123"
        hashed = get_password_hash(test_password)
        print(f"   ✅ 项目密码哈希成功: {hashed[:30]}...")
        
        # 测试密码验证
        is_valid = verify_password(test_password, hashed)
        print(f"   ✅ 项目密码验证成功: {is_valid}")
        
        return True
    except Exception as e:
        print(f"   ❌ 项目security模块测试失败: {e}")
        return False

def test_version_compatibility():
    """测试版本兼容性"""
    print("\n5. 测试版本兼容性...")
    try:
        import bcrypt
        import passlib
        
        bcrypt_version = bcrypt.__version__
        passlib_version = passlib.__version__
        
        print(f"   📦 bcrypt版本: {bcrypt_version}")
        print(f"   📦 passlib版本: {passlib_version}")
        
        # 检查版本兼容性
        bcrypt_major = int(bcrypt_version.split('.')[0])
        passlib_major = int(passlib_version.split('.')[0])
        
        if bcrypt_major >= 4 and passlib_major >= 1:
            print("   ✅ 版本兼容性良好")
            return True
        else:
            print("   ⚠️  版本可能存在兼容性问题")
            return False
            
    except Exception as e:
        print(f"   ❌ 版本兼容性检查失败: {e}")
        return False

def main():
    print("🚀 bcrypt版本兼容性测试...")
    print("=" * 50)
    
    success_count = 0
    total_tests = 5
    
    # 运行所有测试
    if test_bcrypt_import():
        success_count += 1
    
    if test_passlib_import():
        success_count += 1
    
    if test_passlib_bcrypt_context():
        success_count += 1
    
    if test_security_module():
        success_count += 1
    
    if test_version_compatibility():
        success_count += 1
    
    print("\n" + "=" * 50)
    print("🎉 兼容性测试完成！")
    print(f"📊 成功率: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
    
    if success_count == total_tests:
        print("🎯 所有测试通过！bcrypt版本兼容性良好。")
    else:
        print(f"⚠️  有 {total_tests - success_count} 个测试失败，需要调整版本。")
    
    print("\n💡 建议的版本组合:")
    print("   - bcrypt: 4.0.x - 4.1.x")
    print("   - passlib: 1.7.4+")
    print("   - 避免使用bcrypt 4.2.0+（可能有兼容性问题）")

if __name__ == "__main__":
    main()
