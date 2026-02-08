export interface Account {
  id: string;
  name: string;
  account_type: 'checking' | 'savings' | 'credit_card' | 'cash' | 'investment' | 'loan' | 'other';
  balance: number;
  currency: string;
  institution?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  account: string;
  account_name?: string;
  category?: string;
  category_name?: string;
  transaction_type: 'income' | 'expense' | 'transfer';
  amount: number;
  description: string;
  date: string;
  notes?: string;
  created_at: string;
}

export interface Category {
  id: string;
  name: string;
  category_type: 'income' | 'expense';
  icon?: string;
  color?: string;
}

export interface Asset {
  id: string;
  name: string;
  asset_type: string;
  value: number;
  currency: string;
  acquisition_date?: string;
}

export interface Liability {
  id: string;
  name: string;
  liability_type: string;
  amount: number;
  currency: string;
  interest_rate?: number;
  due_date?: string;
}

export interface NetWorth {
  total_assets: number;
  total_liabilities: number;
  net_worth: number;
  currency: string;
  assets_breakdown?: {
    category: string;
    amount: number;
  }[];
  liabilities_breakdown?: {
    category: string;
    amount: number;
  }[];
}
