import React, { useState } from 'react';
import { X, Search, Star, ChevronDown, Check } from 'lucide-react';

/**
 * AJ네트웍스 디자인 시스템 - 공통 컴포넌트 라이브러리
 * 
 * 디자인 토큰:
 * - Primary: #5A7CF0 (파란색)
 * - Brand: #E31E24 (빨간색)
 * - Dark: #3F4654 (다크 그레이)
 * - Error: #FF4D4F (에러 빨간색)
 */

// ========== 디자인 토큰 ==========
const colors = {
  primary: '#5A7CF0',
  brand: '#E31E24',
  dark: '#3F4654',
  error: '#FF4D4F',
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827',
  },
  white: '#FFFFFF',
};

const spacing = {
  xs: '4px',
  sm: '8px',
  md: '12px',
  lg: '16px',
  xl: '24px',
  xxl: '32px',
};

const borderRadius = {
  sm: '4px',
  md: '6px',
  lg: '8px',
};

// ========== 1. Button 컴포넌트 ==========
const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'medium',
  disabled = false,
  onClick,
  icon,
  fullWidth = false,
  ...props 
}) => {
  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    fontWeight: '500',
    border: 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'all 0.2s ease',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", sans-serif',
    width: fullWidth ? '100%' : 'auto',
  };

  const variants = {
    primary: {
      backgroundColor: disabled ? colors.gray[300] : colors.primary,
      color: colors.white,
      ':hover': !disabled && {
        backgroundColor: '#4A6CD4',
        transform: 'translateY(-1px)',
        boxShadow: '0 4px 12px rgba(90, 124, 240, 0.3)',
      },
    },
    secondary: {
      backgroundColor: disabled ? colors.gray[200] : colors.white,
      color: disabled ? colors.gray[400] : colors.gray[700],
      border: `1px solid ${disabled ? colors.gray[300] : colors.gray[300]}`,
      ':hover': !disabled && {
        borderColor: colors.primary,
        color: colors.primary,
      },
    },
    dark: {
      backgroundColor: disabled ? colors.gray[400] : colors.dark,
      color: colors.white,
      ':hover': !disabled && {
        backgroundColor: '#2F3542',
        transform: 'translateY(-1px)',
        boxShadow: '0 4px 12px rgba(63, 70, 84, 0.3)',
      },
    },
    ghost: {
      backgroundColor: 'transparent',
      color: disabled ? colors.gray[400] : colors.gray[700],
      ':hover': !disabled && {
        backgroundColor: colors.gray[100],
      },
    },
  };

  const sizes = {
    small: {
      height: '32px',
      padding: `0 ${spacing.md}`,
      fontSize: '13px',
      borderRadius: borderRadius.sm,
    },
    medium: {
      height: '40px',
      padding: `0 ${spacing.lg}`,
      fontSize: '14px',
      borderRadius: borderRadius.md,
    },
    large: {
      height: '48px',
      padding: `0 ${spacing.xl}`,
      fontSize: '16px',
      borderRadius: borderRadius.lg,
    },
  };

  const [isHovered, setIsHovered] = useState(false);

  const style = {
    ...baseStyles,
    ...variants[variant],
    ...sizes[size],
    ...(isHovered && !disabled && variants[variant][':hover']),
  };

  return (
    <button
      style={style}
      disabled={disabled}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      {...props}
    >
      {icon && icon}
      {children}
    </button>
  );
};

// ========== 2. Input 컴포넌트 ==========
const Input = ({ 
  type = 'text',
  placeholder,
  value,
  onChange,
  error = false,
  disabled = false,
  label,
  helperText,
  clearable = false,
  onClear,
  ...props 
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [internalValue, setInternalValue] = useState(value || '');

  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.xs,
    width: '100%',
  };

  const labelStyle = {
    fontSize: '13px',
    fontWeight: '500',
    color: colors.gray[700],
    fontFamily: '-apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", sans-serif',
  };

  const inputWrapperStyle = {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  };

  const inputStyle = {
    width: '100%',
    height: '40px',
    padding: `0 ${spacing.md}`,
    paddingRight: clearable && internalValue ? '36px' : spacing.md,
    fontSize: '14px',
    border: `1px solid ${
      error ? colors.error : 
      isFocused ? colors.primary : 
      colors.gray[300]
    }`,
    borderRadius: borderRadius.md,
    outline: 'none',
    backgroundColor: disabled ? colors.gray[50] : colors.white,
    color: disabled ? colors.gray[400] : colors.gray[900],
    transition: 'all 0.2s ease',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", sans-serif',
    boxShadow: isFocused ? `0 0 0 3px ${error ? 'rgba(255, 77, 79, 0.1)' : 'rgba(90, 124, 240, 0.1)'}` : 'none',
  };

  const clearButtonStyle = {
    position: 'absolute',
    right: spacing.sm,
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: spacing.xs,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: colors.gray[400],
    transition: 'color 0.2s',
  };

  const helperTextStyle = {
    fontSize: '12px',
    color: error ? colors.error : colors.gray[500],
    fontFamily: '-apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", sans-serif',
  };

  const handleChange = (e) => {
    const newValue = e.target.value;
    setInternalValue(newValue);
    if (onChange) onChange(e);
  };

  const handleClear = () => {
    setInternalValue('');
    if (onClear) onClear();
    if (onChange) onChange({ target: { value: '' } });
  };

  return (
    <div style={containerStyle}>
      {label && <label style={labelStyle}>{label}</label>}
      <div style={inputWrapperStyle}>
        <input
          type={type}
          placeholder={placeholder}
          value={value !== undefined ? value : internalValue}
          onChange={handleChange}
          disabled={disabled}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          style={inputStyle}
          {...props}
        />
        {clearable && internalValue && (
          <button 
            style={clearButtonStyle}
            onClick={handleClear}
            type="button"
            onMouseEnter={(e) => e.target.style.color = colors.gray[600]}
            onMouseLeave={(e) => e.target.style.color = colors.gray[400]}
          >
            <X size={16} />
          </button>
        )}
      </div>
      {helperText && <span style={helperTextStyle}>{helperText}</span>}
    </div>
  );
};

// ========== 3. SearchInput 컴포넌트 ==========
const SearchInput = ({ placeholder = '검색', onSearch, ...props }) => {
  const [value, setValue] = useState('');

  const containerStyle = {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  };

  const iconStyle = {
    position: 'absolute',
    left: spacing.md,
    pointerEvents: 'none',
    color: colors.gray[400],
  };

  const handleSearch = (e) => {
    setValue(e.target.value);
    if (onSearch) onSearch(e.target.value);
  };

  return (
    <div style={containerStyle}>
      <div style={iconStyle}>
        <Search size={16} />
      </div>
      <Input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={handleSearch}
        style={{ paddingLeft: '40px' }}
        {...props}
      />
    </div>
  );
};

// ========== 4. Checkbox 컴포넌트 ==========
const Checkbox = ({ 
  checked = false, 
  onChange, 
  label, 
  disabled = false 
}) => {
  const [isChecked, setIsChecked] = useState(checked);

  const containerStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: spacing.sm,
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.5 : 1,
  };

  const checkboxStyle = {
    width: '18px',
    height: '18px',
    border: `2px solid ${isChecked ? colors.primary : colors.gray[300]}`,
    borderRadius: borderRadius.sm,
    backgroundColor: isChecked ? colors.primary : colors.white,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
    flexShrink: 0,
  };

  const labelStyle = {
    fontSize: '14px',
    color: colors.gray[700],
    userSelect: 'none',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", sans-serif',
  };

  const handleChange = () => {
    if (!disabled) {
      const newChecked = !isChecked;
      setIsChecked(newChecked);
      if (onChange) onChange(newChecked);
    }
  };

  return (
    <div style={containerStyle} onClick={handleChange}>
      <div style={checkboxStyle}>
        {isChecked && <Check size={12} color={colors.white} strokeWidth={3} />}
      </div>
      {label && <span style={labelStyle}>{label}</span>}
    </div>
  );
};

// ========== 5. Badge 컴포넌트 ==========
const Badge = ({ 
  children, 
  variant = 'default',
  size = 'medium' 
}) => {
  const variants = {
    default: {
      backgroundColor: colors.gray[100],
      color: colors.gray[700],
    },
    primary: {
      backgroundColor: colors.primary + '20',
      color: colors.primary,
    },
    success: {
      backgroundColor: '#10B98120',
      color: '#10B981',
    },
    error: {
      backgroundColor: colors.error + '20',
      color: colors.error,
    },
  };

  const sizes = {
    small: {
      padding: `2px ${spacing.sm}`,
      fontSize: '11px',
    },
    medium: {
      padding: `4px ${spacing.md}`,
      fontSize: '12px',
    },
  };

  const badgeStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    fontWeight: '500',
    borderRadius: borderRadius.sm,
    whiteSpace: 'nowrap',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", sans-serif',
    ...variants[variant],
    ...sizes[size],
  };

  return <span style={badgeStyle}>{children}</span>;
};

// ========== 6. Modal 컴포넌트 ==========
const Modal = ({ 
  isOpen, 
  onClose, 
  title, 
  children,
  footer,
  width = '600px',
}) => {
  if (!isOpen) return null;

  const overlayStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    animation: 'fadeIn 0.2s ease',
  };

  const modalStyle = {
    backgroundColor: colors.white,
    borderRadius: borderRadius.lg,
    width: width,
    maxWidth: '90vw',
    maxHeight: '90vh',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    animation: 'slideUp 0.2s ease',
  };

  const headerStyle = {
    padding: spacing.xl,
    borderBottom: `1px solid ${colors.gray[200]}`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  };

  const titleStyle = {
    fontSize: '18px',
    fontWeight: '600',
    color: colors.gray[900],
    fontFamily: '-apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", sans-serif',
  };

  const closeButtonStyle = {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: spacing.xs,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: colors.gray[500],
    transition: 'color 0.2s',
  };

  const contentStyle = {
    padding: spacing.xl,
    flex: 1,
    overflow: 'auto',
  };

  const footerStyle = {
    padding: spacing.xl,
    borderTop: `1px solid ${colors.gray[200]}`,
    display: 'flex',
    gap: spacing.md,
    justifyContent: 'flex-end',
  };

  return (
    <>
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from { transform: translateY(20px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
      `}</style>
      <div style={overlayStyle} onClick={onClose}>
        <div style={modalStyle} onClick={(e) => e.stopPropagation()}>
          <div style={headerStyle}>
            <h2 style={titleStyle}>{title}</h2>
            <button 
              style={closeButtonStyle}
              onClick={onClose}
              onMouseEnter={(e) => e.target.style.color = colors.gray[700]}
              onMouseLeave={(e) => e.target.style.color = colors.gray[500]}
            >
              <X size={20} />
            </button>
          </div>
          <div style={contentStyle}>
            {children}
          </div>
          {footer && (
            <div style={footerStyle}>
              {footer}
            </div>
          )}
        </div>
      </div>
    </>
  );
};

// ========== 7. Pagination 컴포넌트 ==========
const Pagination = ({ 
  currentPage = 1, 
  totalPages = 5, 
  onPageChange 
}) => {
  const containerStyle = {
    display: 'flex',
    gap: spacing.xs,
    alignItems: 'center',
  };

  const pageButtonStyle = (isActive) => ({
    width: '32px',
    height: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: 'none',
    backgroundColor: isActive ? colors.primary : colors.white,
    color: isActive ? colors.white : colors.gray[700],
    cursor: 'pointer',
    borderRadius: borderRadius.sm,
    fontSize: '14px',
    fontWeight: isActive ? '600' : '400',
    transition: 'all 0.2s ease',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", sans-serif',
  });

  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div style={containerStyle}>
      <button
        style={pageButtonStyle(false)}
        onClick={() => currentPage > 1 && onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
      >
        ‹
      </button>
      {pages.map((page) => (
        <button
          key={page}
          style={pageButtonStyle(page === currentPage)}
          onClick={() => onPageChange(page)}
          onMouseEnter={(e) => {
            if (page !== currentPage) {
              e.target.style.backgroundColor = colors.gray[100];
            }
          }}
          onMouseLeave={(e) => {
            if (page !== currentPage) {
              e.target.style.backgroundColor = colors.white;
            }
          }}
        >
          {page}
        </button>
      ))}
      <button
        style={pageButtonStyle(false)}
        onClick={() => currentPage < totalPages && onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
      >
        ›
      </button>
    </div>
  );
};

// ========== 8. Tabs 컴포넌트 ==========
const Tabs = ({ tabs, activeTab, onTabChange }) => {
  const containerStyle = {
    display: 'flex',
    borderBottom: `1px solid ${colors.gray[200]}`,
  };

  const tabStyle = (isActive) => ({
    padding: `${spacing.md} ${spacing.xl}`,
    border: 'none',
    backgroundColor: 'transparent',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: isActive ? '600' : '400',
    color: isActive ? colors.primary : colors.gray[600],
    borderBottom: `2px solid ${isActive ? colors.primary : 'transparent'}`,
    transition: 'all 0.2s ease',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", sans-serif',
    position: 'relative',
    top: '1px',
  });

  return (
    <div style={containerStyle}>
      {tabs.map((tab, index) => (
        <button
          key={index}
          style={tabStyle(activeTab === index)}
          onClick={() => onTabChange(index)}
          onMouseEnter={(e) => {
            if (activeTab !== index) {
              e.target.style.color = colors.gray[900];
            }
          }}
          onMouseLeave={(e) => {
            if (activeTab !== index) {
              e.target.style.color = colors.gray[600];
            }
          }}
        >
          {tab}
        </button>
      ))}
    </div>
  );
};

// ========== 9. FavoriteButton 컴포넌트 ==========
const FavoriteButton = ({ isFavorite = false, onChange }) => {
  const [favorite, setFavorite] = useState(isFavorite);

  const buttonStyle = {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: spacing.xs,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'transform 0.2s ease',
  };

  const handleClick = () => {
    const newFavorite = !favorite;
    setFavorite(newFavorite);
    if (onChange) onChange(newFavorite);
  };

  return (
    <button
      style={buttonStyle}
      onClick={handleClick}
      onMouseEnter={(e) => e.target.style.transform = 'scale(1.1)'}
      onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
    >
      <Star
        size={20}
        fill={favorite ? '#FCD34D' : 'none'}
        color={favorite ? '#FCD34D' : colors.gray[400]}
      />
    </button>
  );
};

// ========== 10. Table 컴포넌트 ==========
const Table = ({ columns, data }) => {
  const tableStyle = {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '14px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", sans-serif',
  };

  const theadStyle = {
    backgroundColor: colors.gray[50],
    borderTop: `1px solid ${colors.gray[200]}`,
    borderBottom: `1px solid ${colors.gray[200]}`,
  };

  const thStyle = {
    padding: spacing.md,
    textAlign: 'left',
    fontWeight: '600',
    color: colors.gray[700],
  };

  const tdStyle = {
    padding: spacing.md,
    borderBottom: `1px solid ${colors.gray[200]}`,
    color: colors.gray[900],
  };

  const rowStyle = {
    transition: 'background-color 0.2s ease',
  };

  return (
    <table style={tableStyle}>
      <thead style={theadStyle}>
        <tr>
          {columns.map((column, index) => (
            <th key={index} style={thStyle}>
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, rowIndex) => (
          <tr
            key={rowIndex}
            style={rowStyle}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = colors.gray[50]}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            {columns.map((column, colIndex) => (
              <td key={colIndex} style={tdStyle}>
                {column.render ? column.render(row) : row[column.key]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

// ========== 데모 애플리케이션 ==========
export default function AJNetworksDesignSystem() {
  const [modalOpen, setModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);

  const demoData = [
    { id: 1, name: '김철수', company: '서울물류', phone: '010-1234-5678' },
    { id: 2, name: '이영희', company: '부산운송', phone: '010-2345-6789' },
    { id: 3, name: '박민수', company: '인천배송', phone: '010-3456-7890' },
  ];

  const columns = [
    { header: '번호', key: 'id' },
    { 
      header: '이름', 
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
          <FavoriteButton />
          {row.name}
        </div>
      )
    },
    { header: '회사명', key: 'company' },
    { header: '연락처', key: 'phone' },
    { 
      header: '액션',
      render: () => (
        <div style={{ display: 'flex', gap: spacing.sm }}>
          <Button size="small" variant="ghost">선택</Button>
        </div>
      )
    },
  ];

  return (
    <div style={{ 
      padding: spacing.xxl,
      maxWidth: '1400px',
      margin: '0 auto',
      backgroundColor: colors.gray[50],
      minHeight: '100vh',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", sans-serif',
    }}>
      {/* 헤더 */}
      <div style={{
        backgroundColor: colors.white,
        padding: spacing.xl,
        borderRadius: borderRadius.lg,
        marginBottom: spacing.xl,
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: spacing.md,
          marginBottom: spacing.md,
        }}>
          <div style={{
            backgroundColor: colors.brand,
            color: colors.white,
            padding: `${spacing.sm} ${spacing.lg}`,
            borderRadius: borderRadius.md,
            fontSize: '20px',
            fontWeight: '700',
          }}>
            AJ네트웍스
          </div>
          <h1 style={{
            fontSize: '24px',
            fontWeight: '600',
            color: colors.gray[900],
            margin: 0,
          }}>
            공통 컴포넌트 디자인 시스템
          </h1>
        </div>
        <p style={{
          color: colors.gray[600],
          margin: 0,
          fontSize: '14px',
        }}>
          운송 관리 시스템을 위한 표준 UI 컴포넌트 라이브러리
        </p>
      </div>

      {/* 버튼 섹션 */}
      <div style={{
        backgroundColor: colors.white,
        padding: spacing.xl,
        borderRadius: borderRadius.lg,
        marginBottom: spacing.xl,
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      }}>
        <h2 style={{
          fontSize: '18px',
          fontWeight: '600',
          color: colors.gray[900],
          marginTop: 0,
          marginBottom: spacing.lg,
        }}>
          1. 버튼 컴포넌트
        </h2>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: spacing.md,
          alignItems: 'center',
        }}>
          <Button variant="primary">운송신청</Button>
          <Button variant="secondary">취소</Button>
          <Button variant="dark">등록</Button>
          <Button variant="ghost">고객해제</Button>
          <Button variant="primary" disabled>비활성</Button>
          <Button variant="primary" size="small">소형 버튼</Button>
          <Button variant="primary" size="large">대형 버튼</Button>
        </div>
      </div>

      {/* 입력 필드 섹션 */}
      <div style={{
        backgroundColor: colors.white,
        padding: spacing.xl,
        borderRadius: borderRadius.lg,
        marginBottom: spacing.xl,
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      }}>
        <h2 style={{
          fontSize: '18px',
          fontWeight: '600',
          color: colors.gray[900],
          marginTop: 0,
          marginBottom: spacing.lg,
        }}>
          2. 입력 필드 컴포넌트
        </h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: spacing.lg,
        }}>
          <Input 
            label="이름" 
            placeholder="이름을 입력하세요"
            clearable
          />
          <Input 
            label="전화번호" 
            placeholder="010-0000-0000"
            helperText="하이픈(-) 포함 입력"
          />
          <Input 
            label="에러 상태" 
            placeholder="잘못된 입력"
            error
            helperText="필수 입력 항목입니다"
          />
          <SearchInput placeholder="고객명 검색" />
        </div>
      </div>

      {/* 체크박스 & 뱃지 섹션 */}
      <div style={{
        backgroundColor: colors.white,
        padding: spacing.xl,
        borderRadius: borderRadius.lg,
        marginBottom: spacing.xl,
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      }}>
        <h2 style={{
          fontSize: '18px',
          fontWeight: '600',
          color: colors.gray[900],
          marginTop: 0,
          marginBottom: spacing.lg,
        }}>
          3. 체크박스 & 뱃지
        </h2>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: spacing.lg,
        }}>
          <div style={{ display: 'flex', gap: spacing.xl, flexWrap: 'wrap' }}>
            <Checkbox label="전체 선택" />
            <Checkbox label="운송 완료" checked />
            <Checkbox label="비활성 상태" disabled />
          </div>
          <div style={{ display: 'flex', gap: spacing.md, flexWrap: 'wrap' }}>
            <Badge variant="default">기본</Badge>
            <Badge variant="primary">진행중</Badge>
            <Badge variant="success">완료</Badge>
            <Badge variant="error">취소</Badge>
          </div>
        </div>
      </div>

      {/* 탭 & 페이지네이션 섹션 */}
      <div style={{
        backgroundColor: colors.white,
        padding: spacing.xl,
        borderRadius: borderRadius.lg,
        marginBottom: spacing.xl,
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      }}>
        <h2 style={{
          fontSize: '18px',
          fontWeight: '600',
          color: colors.gray[900],
          marginTop: 0,
          marginBottom: spacing.lg,
        }}>
          4. 탭 & 페이지네이션
        </h2>
        <Tabs
          tabs={['상차지', '하차지', '경유지']}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
        <div style={{ 
          padding: spacing.xl,
          color: colors.gray[700],
        }}>
          {activeTab === 0 && '상차지 컨텐츠'}
          {activeTab === 1 && '하차지 컨텐츠'}
          {activeTab === 2 && '경유지 컨텐츠'}
        </div>
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          paddingTop: spacing.lg,
        }}>
          <Pagination
            currentPage={currentPage}
            totalPages={5}
            onPageChange={setCurrentPage}
          />
        </div>
      </div>

      {/* 테이블 섹션 */}
      <div style={{
        backgroundColor: colors.white,
        padding: spacing.xl,
        borderRadius: borderRadius.lg,
        marginBottom: spacing.xl,
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      }}>
        <h2 style={{
          fontSize: '18px',
          fontWeight: '600',
          color: colors.gray[900],
          marginTop: 0,
          marginBottom: spacing.lg,
        }}>
          5. 테이블 컴포넌트
        </h2>
        <Table columns={columns} data={demoData} />
      </div>

      {/* 모달 섹션 */}
      <div style={{
        backgroundColor: colors.white,
        padding: spacing.xl,
        borderRadius: borderRadius.lg,
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      }}>
        <h2 style={{
          fontSize: '18px',
          fontWeight: '600',
          color: colors.gray[900],
          marginTop: 0,
          marginBottom: spacing.lg,
        }}>
          6. 모달 컴포넌트
        </h2>
        <Button onClick={() => setModalOpen(true)}>
          거래처 선택 모달 열기
        </Button>
      </div>

      {/* 모달 */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="거래처 선택"
        footer={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>
              취소
            </Button>
            <Button variant="primary" onClick={() => setModalOpen(false)}>
              선택
            </Button>
          </>
        }
      >
        <div style={{ padding: spacing.lg }}>
          <SearchInput placeholder="거래처 검색" />
          <div style={{ marginTop: spacing.xl }}>
            <Table columns={columns} data={demoData} />
          </div>
        </div>
      </Modal>
    </div>
  );
}
