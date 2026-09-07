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
        this.selectedLocation = locations[0] ?? null;
      })
      .catch(() => {
        this.errorMessage = 'Unable to load locations. Check the admin key and API connection.';
      })
      .finally(() => {
        this.isLoading = false;
      });
  }

  selectLocation(location: LocationRecord): void {
    this.selectedLocation = location;
  }

}
