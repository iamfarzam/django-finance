export * from './finance';
export * from './social';

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  is_active: boolean;
  date_joined: string;
}

export interface DashboardStats {
  accounts_count: number;
  transactions_count: number;
  contacts_count: number;
  active_debts_count: number;
}

export interface DashboardData {
  user: User;
  net_worth: {
    total_assets: number;
    total_liabilities: number;
    net_worth: number;
    currency: string;
  };
  stats: DashboardStats;
  recent_transactions: Array<{
    id: string;
    description: string;
    amount: number;
    transaction_type: 'income' | 'expense' | 'transfer';
    date: string;
    account_name?: string;
    category_name?: string;
  }>;
  social: {
    total_they_owe: number;
    total_you_owe: number;
    net_balance: number;
    currency: string;
  };
}
