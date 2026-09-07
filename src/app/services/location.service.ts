import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export interface LocationRecord {
  id: number;
  latitude: number;
  longitude: number;
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class LocationService {
  private readonly apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  getPosition(): Promise<{ lat: number; lng: number }> {
    return new Promise((resolve, reject) => {
      if (typeof navigator === 'undefined' || !navigator.geolocation) {
        reject('Geolocation is not supported by this browser.');
        return;
      }

      navigator.geolocation.getCurrentPosition(
          (position) => {
            resolve({
              lat: position.coords.latitude,
              lng: position.coords.longitude
            });
          },
          (error) => {
            reject(`Geolocation error: ${error.message}`);
          }
      );
    });
  }

  savePosition(position: { lat: number; lng: number }): Promise<LocationRecord> {
    return firstValueFrom(this.http.post<LocationRecord>(`${this.apiUrl}/api/locations`, {
      latitude: position.lat,
      longitude: position.lng
    }));
  }

  getLocations(adminKey: string): Promise<LocationRecord[]> {
    return firstValueFrom(this.http.get<LocationRecord[]>(`${this.apiUrl}/api/locations`, {
      headers: { 'X-Admin-Key': adminKey }
    }));
  }
}