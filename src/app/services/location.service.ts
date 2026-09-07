import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';

export interface LocationRecord {
  id: number;
  latitude: number | null;
  longitude: number | null;
  created_at: string;
  status: 'allowed' | 'not_allowed';
}

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface Headline {
  title: string;
  source: string;
  url: string;
  published_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class LocationService {
  private readonly apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  watchPosition(onPosition: (position: Coordinates) => void, onError: (error: string) => void): number | null {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      onError('Geolocation is not supported by this browser.');
      return null;
    }

    return navigator.geolocation.watchPosition(
      (position) => onPosition({ lat: position.coords.latitude, lng: position.coords.longitude }),
      (error) => onError(`Geolocation error: ${error.message}`),
      { enableHighAccuracy: false, maximumAge: 30000, timeout: 10000 }
    );
  }

  clearPositionWatch(watchId: number | null): void {
    if (watchId !== null && typeof navigator !== 'undefined' && navigator.geolocation) {
      navigator.geolocation.clearWatch(watchId);
    }
  }

  getClientId(): string {
    const storageKey = 'location-client-id';
    if (typeof localStorage === 'undefined') {
      return crypto.randomUUID();
    }

    let clientId = localStorage.getItem(storageKey);
    if (!clientId) {
      clientId = crypto.randomUUID();
      localStorage.setItem(storageKey, clientId);
    }
    return clientId;
  }

  getPosition(): Promise<Coordinates> {
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

  savePosition(position: Coordinates, clientId: string): Promise<LocationRecord> {
    return firstValueFrom(this.http.post<LocationRecord>(`${this.apiUrl}/api/locations`, {
      latitude: position.lat,
      longitude: position.lng,
      client_id: clientId,
      status: 'allowed'
    }));
  }

  savePermissionStatus(clientId: string, status: 'not_allowed'): Promise<LocationRecord> {
    return firstValueFrom(this.http.post<LocationRecord>(`${this.apiUrl}/api/locations`, {
      client_id: clientId,
      status
    }));
  }

  getLocations(adminKey: string): Promise<LocationRecord[]> {
    return firstValueFrom(this.http.get<LocationRecord[]>(`${this.apiUrl}/api/locations`, {
      headers: { 'X-Admin-Key': adminKey }
    }));
  }

  deleteLocation(adminKey: string, locationId: number): Promise<void> {
    return firstValueFrom(this.http.delete<void>(`${this.apiUrl}/api/locations/${locationId}`, {
      headers: { 'X-Admin-Key': adminKey }
    }));
  }

  getHeadlines(position?: Coordinates): Promise<Headline[]> {
    const query = position ? `?latitude=${position.lat}&longitude=${position.lng}` : '';
    return firstValueFrom(this.http.get<Headline[]>(`${this.apiUrl}/api/headlines${query}`));
  }
}