export interface Contact {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  notes?: string;
  created_at: string;
}

export interface PeerDebt {
  id: string;
  contact: string;
  contact_name?: string;
  debt_type: 'owed_to_me' | 'owed_by_me';
  amount: number;
  currency: string;
  description: string;
  due_date?: string;
  is_settled: boolean;
  created_at: string;
}

export interface Balance {
  contact_id: string;
  contact_name: string;
  they_owe: number;
  you_owe: number;
  net_balance: number;
  currency: string;
}

export interface ExpenseGroup {
  id: string;
  name: string;
  description?: string;
  members: string[];
  total_expenses: number;
  created_at: string;
}

export interface Settlement {
  id: string;
  from_contact: string;
  to_contact: string;
  amount: number;
  currency: string;
  settled_at: string;
}

export interface SocialSummary {
  total_they_owe: number;
  total_you_owe: number;
  net_balance: number;
  currency: string;
  active_debts_count: number;
  contacts_count: number;
}
