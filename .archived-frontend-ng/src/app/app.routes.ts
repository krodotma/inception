import { Routes } from '@angular/router';

export const routes: Routes = [
    {
        path: '',
        loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
        title: 'Dashboard - Inception'
    },
    {
        path: 'explorer',
        loadComponent: () => import('./pages/explorer/explorer.component').then(m => m.ExplorerComponent),
        title: 'Explorer - Inception'
    },
    {
        path: 'terminal',
        loadComponent: () => import('./pages/terminal/terminal.component').then(m => m.TerminalComponent),
        title: 'Terminal - Inception'
    },
    {
        path: 'settings',
        loadComponent: () => import('./pages/settings/settings.component').then(m => m.SettingsComponent),
        title: 'Settings - Inception'
    },
    {
        path: '**',
        redirectTo: ''
    }
];
