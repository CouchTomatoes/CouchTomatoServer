using System.Linq.Expressions;
using CouchTomato.Data.Entities;

namespace CouchTomato.Core.Interfaces;

public interface IEntityBaseRepository<T> where T : class, IEntityBase
{
    IQueryable<T> All { get; }

    Task<T> AddAsync(T entity);
    Task<List<T>> GetAllAsync();
    Task<T?> GetByIdAsync(Guid id);

    // Optional common queries
    //Task<List<T>> FindAsync(Expression<Func<T, bool>> predicate);

    void SoftDelete(T entity);
    Task SaveAsync();
}
