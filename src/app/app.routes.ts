import { Routes } from '@angular/router';
import { AdminComponent } from './admin/admin.component';
import { LocationHomeComponent } from './location-home/location-home.component';

export const routes: Routes = [
	{ path: '', component: LocationHomeComponent },
	{ path: 'admin', component: AdminComponent }
];
