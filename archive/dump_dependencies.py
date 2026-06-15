import os

files_to_read = [
    'src/app/page.tsx',
    'src/app/subscriptions/page.tsx',
    'src/app/transactions/page.tsx',
    'src/app/wealth/page.tsx',
    'src/app/wealth/allocation/page.tsx',
    'src/app/wealth/asset/[ticker]/page.tsx',
    'src/app/wealth/dividends/page.tsx',
    'src/app/wealth/evolution/page.tsx',
    'src/app/wealth/patrimonio/page.tsx',
    'src/components/dashboard/DashboardPage.tsx',
    'src/components/dashboard/SummaryCards.tsx',
    'src/components/dashboard/CategoriesCard.tsx',
    'src/components/dashboard/InstallmentCard.tsx',
    'src/components/dashboard/PacingCard.tsx',
    'src/components/dashboard/AllocationChart.tsx',
    'src/hooks/useAdminCRUD.ts',
    'src/hooks/useAllocationData.ts',
    'src/hooks/useAlphaData.ts',
    'src/hooks/useAudit.ts',
    'src/hooks/useCategoriesAdmin.ts',
    'src/hooks/useDividendsAdmin.ts',
    'src/hooks/useDividendsData.ts',
    'src/hooks/useGrowthData.ts',
    'src/hooks/usePositionsAdmin.ts',
    'src/hooks/useTransactions.ts',
    'src/hooks/useWealthStore.ts',
    'src/types/entities.ts',
    'src/types/dto.ts'
]

base_dir = r'C:\Users\Cleidson\Pictures\fin_analytics_v2\frontend'
out_path = r'C:\Users\Cleidson\Pictures\fin_analytics_v2\dependency_data.txt'

with open(out_path, 'w', encoding='utf-8') as out_file:
    for f in files_to_read:
        path = os.path.join(base_dir, f)
        if os.path.exists(path):
            out_file.write(f'==== {f} ====\n')
            with open(path, 'r', encoding='utf-8') as in_file:
                out_file.write(in_file.read())
                out_file.write('\n\n')
