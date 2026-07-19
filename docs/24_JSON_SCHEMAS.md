> [!IMPORTANT]
> A pasta `docs/` é a única fonte oficial de documentação do projeto.

# JSON Schemas (Pierre Finance)

## Account [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## Balance [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## AccountBalance [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## Transaction [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## FriendlyTransactionData [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## InstallmentStats [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## InstallmentSummary [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## InstallmentPurchase [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## Bill [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## BillSummary [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## ManageClosingDateRequest [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## ListAccountsResponse [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## ClosingDateOperationResponse [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## ManualUpdateDetails [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## SyncResultItem [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## SpendingLimit [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## SpendingLimitWithUsage [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## SpendingLimitStatus [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## SpendingLimitQuota [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## CreateSpendingLimitRequest [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## UpdateSpendingLimitRequest [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## PaymentReminder [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
- `id` (string): Opcional. 
- `title` (string): Opcional. 
- `amount` (number): Opcional. 
- `dueDate` (string): Opcional. 
- `reminderTime` (string): Opcional. 
- `status` (string): Opcional. 
- `isRecurring` (boolean): Opcional. 
- `recurrencePattern` (string): Opcional. 
- `createdAt` (string): Opcional. 

## CreatePaymentReminderRequest [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
- `title` (string): Obrigatório. 
- `amount` (number): Opcional. 
- `dueDate` (string): Obrigatório. 
- `reminderTime` (string): Opcional. 
- `isRecurring` (boolean): Opcional. 
- `recurrencePattern` (string): Opcional. 

## UpdatePaymentReminderRequest [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
- `reminderId` (string): Obrigatório. 
- `title` (string): Opcional. 
- `amount` (number): Opcional. 
- `dueDate` (string): Opcional. 
- `reminderTime` (string): Opcional. 
- `newStatus` (string): Opcional. 

## PaymentReminderQuota [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
- `subscriptionType` (string): Opcional. 
- `currentCount` (number): Opcional. 
- `limit` (number): Opcional. 
- `canCreate` (boolean): Opcional. 
- `remaining` (number): Opcional. 

## AuthError [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

## ServerError [CONFIRMADO]
- **Type:** object
- **Description:** 

### Campos
Nenhum campo documentado.

