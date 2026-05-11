"""
AuditLink — Sample Data Generator (Simple Demo)
═══════════════════════════════════════════════════
Creates minimal sample Excel files for quick system testing.
For real audits, upload the actual reports through the UI.
"""

import pandas as pd
import os

OUTPUT_DIR = os.path.dirname(__file__)


def generate_all():
    """Generate minimal sample files for demo purposes."""
    _generate_gosi_file()
    _generate_medical_file()
    _generate_payroll_file()
    _generate_muqeem_file()
    print("✅ تم إنشاء ملفات العينة التجريبية بنجاح!")


def _generate_gosi_file():
    data = {
        'رقم الهوية': ['1000000001', '1000000002', '1000000003', '2000000001', '2000000002', '2000000003'],
        'اسم المشترك': ['أحمد محمد', 'سارة عبدالله', 'خالد ناصر', 'John Smith', 'Ali Hassan', 'Raj Patel'],
        'حالة المشترك': ['نشط', 'نشط', 'نشط', 'نشط', 'نشط', 'غير نشط'],
        'الجنسية': ['السعودية', 'السعودية', 'السعودية', 'أمريكي', 'مصري', 'هندي'],
        'الجنس': ['ذكر', 'انثى', 'ذكر', 'ذكر', 'ذكر', 'ذكر'],
        'المهنة': ['مهندس', 'محاسب', 'مهندس', 'مهندس', 'فني', 'عامل'],
        'تاريخ الإلتحاق': ['2024-01-01'] * 6,
    }
    pd.DataFrame(data).to_excel(os.path.join(OUTPUT_DIR, 'gosi_file.xlsx'), index=False)


def _generate_medical_file():
    data = {
        'Iqama No': ['1000000001', '1000000002', '2000000001', '3000000001', '3000000002', '9000000001'],
        'Member Name': ['أحمد محمد', 'سارة عبدالله', 'John Smith', 'زوجة أحمد', 'ابن سارة', 'موظف سابق'],
        'Inception': ['01-01-2025'] * 6,
        'Class': ['A', 'A', 'B', 'B', 'B', 'A'],
        'Relation': ['1', '1', '1', '2', '3', '1'],
        'Gender': ['M', 'F', 'M', 'F', 'M', 'M'],
        'Staff No': ['EMP001', 'EMP002', 'EMP004', '', '', 'EMP099'],
        'Type': ['سنوي'] * 6,
        'Premium': ['3000', '3000', '1500', '1200', '800', '2000'],
        'DOB': ['1990-01-01', '1992-05-15', '1988-03-20', '1991-07-10', '2015-02-28', '1985-11-05'],
        'CCHI Si': ['CCI001', 'CCI002', 'CCI003', 'CCI004', 'CCI005', 'CCI006'],
    }
    pd.DataFrame(data).to_excel(os.path.join(OUTPUT_DIR, 'medical_file.xlsx'), index=False)


def _generate_payroll_file():
    data = {
        'رقم الهوية': ['1000000001', '1000000002', '1000000003', '2000000001', '2000000002', '9900000001'],
        'Employees Number': ['EMP001', 'EMP002', 'EMP003', 'EMP004', 'EMP005', 'EMP006'],
        'ARABIC NAME': ['أحمد محمد', 'سارة عبدالله', 'خالد ناصر', 'جون سميث', 'علي حسن', 'موظف جديد'],
        'NAME': ['Ahmad', 'Sarah', 'Khaled', 'John', 'Ali', 'New Hire'],
        'START UP DATE': ['12/15/2024'] * 5 + ['03/15/2025'],
        'الوظيفة': ['مهندس', 'محاسب', 'مهندس', 'فني', 'مشرف', 'عامل'],
        'الشعبة': ['الكهرباء', 'المالية', 'الميكانيكا', 'الكهرباء', 'المشاريع', 'الكهرباء'],
        'DEGREE': ['10', '8', '10', '6', '7', '3'],
    }
    pd.DataFrame(data).to_excel(os.path.join(OUTPUT_DIR, 'payroll_file.xlsx'), index=False)


def _generate_muqeem_file():
    data = {
        'رقم الاقامة': ['2000000001', '2000000002', '2000000003'],
        'الاسم': ['John Smith', 'Ali Hassan', 'Raj Patel'],
        'الجنس': ['ذكر', 'ذكر', 'ذكر'],
        'الجنسية': ['أمريكي', 'مصري', 'هندي'],
        'المهنة': ['مهندس', 'فني', 'عامل'],
        'رقم الجواز': ['P123456', 'P234567', 'P345678'],
        'اصدار الاقامة': ['2024-01-01'] * 3,
        'انتهاء الاقامة': ['2026-01-01'] * 3,
        'تاريخ الميلاد': ['1988-03-20', '1990-06-15', '1985-09-10'],
        'رقم صاحب العمل': ['7042607833'] * 3,
    }
    pd.DataFrame(data).to_excel(os.path.join(OUTPUT_DIR, 'muqeem_file.xlsx'), index=False)


if __name__ == '__main__':
    generate_all()
