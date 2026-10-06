import React from 'react';
import {
  Home,
  Utensils,
  Car,
  Gamepad2,
  Receipt,
  HeartPulse,
  GraduationCap,
  Briefcase,
  Wrench,
  ShoppingBag,
  TrendingUp,
  PlusCircle,
  Tag,
  CreditCard,
  Wallet,
  Landmark,
  Tv,
  Wifi,
  Smartphone,
  Sparkles,
  MoreHorizontal
} from 'lucide-react';

export function formatCurrency(amount, currency = 'BRL') {
  if (amount === null || amount === undefined || isNaN(amount)) return 'R$ 0,00';
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: currency === 'USD' ? 'USD' : currency === 'EUR' ? 'EUR' : 'BRL',
  }).format(amount);
}

export function formatDate(dateString) {
  if (!dateString) return '';
  const [year, month, day] = String(dateString).split('T')[0].split('-');
  return `${day}/${month}/${year}`;
}

export function formatShortDate(dateString) {
  if (!dateString) return '';
  const [year, month, day] = String(dateString).split('T')[0].split('-');
  return `${day}/${month}`;
}

export function getCategoryIcon(iconName, className = "w-5 h-5") {
  switch ((iconName || '').toLowerCase()) {
    case 'home':
    case 'moradia':
      return <Home className={className} />;
    case 'utensils':
    case 'alimentação':
    case 'restaurante':
      return <Utensils className={className} />;
    case 'car':
    case 'transporte':
      return <Car className={className} />;
    case 'gamepad2':
    case 'lazer':
      return <Gamepad2 className={className} />;
    case 'receipt':
    case 'contas':
    case 'luz':
      return <Receipt className={className} />;
    case 'heartpulse':
    case 'saúde':
      return <HeartPulse className={className} />;
    case 'graduationcap':
    case 'educação':
      return <GraduationCap className={className} />;
    case 'briefcase':
    case 'salário':
      return <Briefcase className={className} />;
    case 'wrench':
    case 'serviços':
      return <Wrench className={className} />;
    case 'shoppingbag':
    case 'vendas':
    case 'mercado':
      return <ShoppingBag className={className} />;
    case 'trendingup':
    case 'rendimentos':
      return <TrendingUp className={className} />;
    case 'wifi':
    case 'internet':
      return <Wifi className={className} />;
    case 'tv':
    case 'netflix':
      return <Tv className={className} />;
    case 'smartphone':
    case 'celular':
      return <Smartphone className={className} />;
    case 'creditcard':
    case 'cartão':
    case 'fatura':
      return <CreditCard className={className} />;
    case 'wallet':
    case 'carteira':
      return <Wallet className={className} />;
    case 'landmark':
    case 'banco':
    case 'conta':
      return <Landmark className={className} />;
    default:
      return <Tag className={className} />;
  }
}
