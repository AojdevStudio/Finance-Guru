CREATE TYPE "public"."account_type" AS ENUM('depository', 'credit', 'loan', 'investment', 'other');--> statement-breakpoint
CREATE TYPE "public"."connection_status" AS ENUM('connected', 'disconnected');--> statement-breakpoint
CREATE TYPE "public"."transaction_method" AS ENUM('payment', 'card_purchase', 'card_payment', 'transfer', 'ach', 'wire', 'atm', 'fee', 'interest', 'deposit', 'withdrawal', 'other');--> statement-breakpoint
CREATE TYPE "public"."transaction_status" AS ENUM('pending', 'posted');--> statement-breakpoint
CREATE TABLE "bank_accounts" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"bank_connection_id" uuid NOT NULL,
	"account_id" text NOT NULL,
	"name" text NOT NULL,
	"official_name" text,
	"type" "account_type" NOT NULL,
	"subtype" text,
	"mask" text,
	"currency" text DEFAULT 'USD' NOT NULL,
	"current_balance" numeric(12, 2),
	"available_balance" numeric(12, 2),
	"enabled" boolean DEFAULT true NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "bank_accounts_account_id_unique" UNIQUE("account_id")
);
--> statement-breakpoint
CREATE TABLE "bank_connections" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"institution_id" text NOT NULL,
	"item_id" text NOT NULL,
	"access_token" text NOT NULL,
	"name" text NOT NULL,
	"logo_url" text,
	"status" "connection_status" DEFAULT 'connected' NOT NULL,
	"last_synced_at" timestamp with time zone,
	"error_details" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "bank_connections_item_id_unique" UNIQUE("item_id")
);
--> statement-breakpoint
CREATE TABLE "transactions" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"bank_account_id" uuid NOT NULL,
	"plaid_transaction_id" text NOT NULL,
	"date" date NOT NULL,
	"name" text NOT NULL,
	"description" text,
	"merchant_name" text,
	"amount" numeric(12, 2) NOT NULL,
	"currency" text DEFAULT 'USD' NOT NULL,
	"category" text,
	"category_detailed" text,
	"method" "transaction_method" DEFAULT 'other',
	"status" "transaction_status" DEFAULT 'posted' NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "transactions_plaid_transaction_id_unique" UNIQUE("plaid_transaction_id")
);
--> statement-breakpoint
ALTER TABLE "bank_accounts" ADD CONSTRAINT "bank_accounts_bank_connection_id_bank_connections_id_fk" FOREIGN KEY ("bank_connection_id") REFERENCES "public"."bank_connections"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "transactions" ADD CONSTRAINT "transactions_bank_account_id_bank_accounts_id_fk" FOREIGN KEY ("bank_account_id") REFERENCES "public"."bank_accounts"("id") ON DELETE cascade ON UPDATE no action;
