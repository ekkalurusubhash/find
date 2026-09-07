import { Component } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LocationMapComponent } from '../location-map/location-map.component';
import { LocationRecord, LocationService } from '../services/location.service';

@Component({
  selector: 'app-admin',
  imports: [DatePipe, DecimalPipe, FormsModule, LocationMapComponent],
  templateUrl: './admin.component.html',
  styleUrl: './admin.component.scss'
})
export class AdminComponent {
  adminKey = '';
  locations: LocationRecord[] = [];
  selectedLocation: LocationRecord | null = null;
  errorMessage: string | null = null;
  isLoading = false;
  deletingLocationId: number | null = null;

  constructor(private locationService: LocationService) {}

  loadLocations(): void {
    if (!this.adminKey.trim()) {
      this.errorMessage = 'Enter the admin API key to continue.';
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;
    this.locationService.getLocations(this.adminKey.trim())
      .then((locations) => {
        this.locations = locations;
        this.selectedLocation = locations.find((location) => location.status === 'allowed') ?? null;
      })
      .catch((error: { status?: number; error?: { detail?: string } }) => {
        this.errorMessage = error.error?.detail
          ?? `Unable to load locations (HTTP ${error.status ?? 'unknown'}). Check the admin key and API connection.`;
      })
      .finally(() => {
        this.isLoading = false;
      });
  }

  selectLocation(location: LocationRecord): void {
    if (location.status === 'allowed') {
      this.selectedLocation = location;
    }
  }

  deleteLocation(location: LocationRecord): void {
    if (!this.adminKey.trim() || !window.confirm('Delete this location record?')) {
      return;
    }

    this.deletingLocationId = location.id;
    this.errorMessage = null;
    this.locationService.deleteLocation(this.adminKey.trim(), location.id)
      .then(() => {
        this.locations = this.locations.filter((item) => item.id !== location.id);
        if (this.selectedLocation?.id === location.id) {
          this.selectedLocation = this.locations.find((item) => item.status === 'allowed') ?? null;
        }
      })
      .catch((error: { status?: number; error?: { detail?: string } }) => {
        this.errorMessage = error.error?.detail
          ?? `Unable to delete location (HTTP ${error.status ?? 'unknown'}).`;
      })
      .finally(() => {
        this.deletingLocationId = null;
      });
  }

}
